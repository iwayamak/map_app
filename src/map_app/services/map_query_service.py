import json

from django.db.models import Count, F, OuterRef, Prefetch, Q, Subquery, TextField
from django.db.models.functions import Cast

from map_app.domain import get_activity_log_item_model, get_activity_log_model, get_location_model, get_tag_model
from map_app.domain_terms import get_domain_term_bool
from map_app.services.map_tag_service import normalize_selected_tags, split_selected_tags


def filter_locations_queryset(location_qs, search_query="", selected_tags=None, domain_terms=None):
    Location = get_location_model()
    search_query = (search_query or "").strip()
    selected_tags = normalize_selected_tags(selected_tags, domain_terms=domain_terms)

    if selected_tags:
        matching_location_ids = (
            Location.objects.filter(tags__name__in=selected_tags)
            .annotate(
                matched_tag_count=Count(
                    "tags__name",
                    filter=Q(tags__name__in=selected_tags),
                    distinct=True,
                )
            )
            .filter(matched_tag_count=len(selected_tags))
            .values("id")
        )
        location_qs = location_qs.filter(id__in=matching_location_ids)

    if search_query:
        escaped_search_query = json.dumps(search_query, ensure_ascii=True).strip('"')
        location_qs = location_qs.annotate(
            location_custom_data_text=Cast("custom_data", output_field=TextField())
        )
        location_qs = location_qs.filter(
            Q(name__icontains=search_query)
            | Q(tags__name__icontains=search_query)
            | Q(location_custom_data_text__icontains=search_query)
            | Q(location_custom_data_text__icontains=escaped_search_query)
        )

    return location_qs.distinct()


def get_filtered_activity_log_queryset(search_query="", selected_tags=None, domain_terms=None):
    ActivityLog = get_activity_log_model()
    ActivityLogItem = get_activity_log_item_model()
    Location = get_location_model()
    search_query = (search_query or "").strip()
    selected_tags, include_unvisited_only, include_domain_info_only = split_selected_tags(
        selected_tags,
        domain_terms=domain_terms,
    )
    if include_unvisited_only:
        return ActivityLog.objects.none()

    activity_log_qs = ActivityLog.objects.select_related("location").order_by("date", "id")

    if include_domain_info_only:
        first_activity_log_id_subquery = (
            ActivityLog.objects.filter(location_id=OuterRef("location_id"))
            .order_by("date", "id")
            .values("id")[:1]
        )
        activity_log_qs = activity_log_qs.annotate(
            first_activity_log_id=Subquery(first_activity_log_id_subquery)
        ).filter(id=F("first_activity_log_id"))

    if selected_tags:
        activity_log_qs = activity_log_qs.filter(
            location_id__in=filter_locations_queryset(
                Location.objects.all(),
                selected_tags=selected_tags,
                domain_terms=domain_terms,
            ).values("id")
        )

    use_record_items = get_domain_term_bool(domain_terms, "use_record_items", default=True)
    if use_record_items:
        activity_log_qs = activity_log_qs.prefetch_related(
            Prefetch(
                "activitylogitem_set",
                queryset=ActivityLogItem.objects.select_related("item").order_by("order"),
            )
        )

    if search_query:
        escaped_search_query = json.dumps(search_query, ensure_ascii=True).strip('"')
        activity_log_qs = activity_log_qs.annotate(
            activity_custom_data_text=Cast("custom_data", output_field=TextField()),
            location_custom_data_text=Cast("location__custom_data", output_field=TextField()),
        )
        query = (
            Q(location__name__icontains=search_query)
            | Q(location__tags__name__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(activity_custom_data_text__icontains=search_query)
            | Q(location_custom_data_text__icontains=search_query)
            | Q(activity_custom_data_text__icontains=escaped_search_query)
            | Q(location_custom_data_text__icontains=escaped_search_query)
        )
        if use_record_items:
            query |= Q(activitylogitem__item__name__icontains=search_query)
        activity_log_qs = activity_log_qs.filter(query)
    return activity_log_qs.distinct()


def get_filtered_unvisited_location_queryset(search_query="", selected_tags=None, domain_terms=None):
    Location = get_location_model()
    Tag = get_tag_model()
    selected_tags, include_unvisited, include_domain_info_only = split_selected_tags(
        selected_tags,
        domain_terms=domain_terms,
    )
    if include_domain_info_only and not include_unvisited:
        return Location.objects.none()
    base_qs = (
        Location.objects.annotate(activity_log_count=Count("activity_logs", distinct=True))
        .filter(activity_log_count=0)
        .prefetch_related(
            Prefetch(
                "tags",
                queryset=Tag.objects.only("id", "name").order_by("order", "name"),
            )
        )
        .order_by("name", "id")
    )
    return filter_locations_queryset(
        base_qs,
        search_query=search_query,
        selected_tags=selected_tags,
        domain_terms=domain_terms,
    )


get_filtered_performance_queryset = get_filtered_activity_log_queryset
