import json

from django.db.models import Count, Exists, F, OuterRef, Prefetch, Q, Subquery, TextField
from django.db.models.functions import Cast

from map_app.domain import get_activity_log_model, get_location_model, get_tag_model
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


def get_filtered_performance_queryset(search_query="", selected_tags=None, domain_terms=None):
    ActivityLog = get_activity_log_model()
    Location = get_location_model()
    Tag = get_tag_model()
    search_query = (search_query or "").strip()
    selected_tags, include_unvisited_only, include_domain_info_only = split_selected_tags(
        selected_tags,
        domain_terms=domain_terms,
    )
    if include_unvisited_only:
        return ActivityLog.objects.none()

    performance_qs = (
        ActivityLog.objects.select_related("location")
        .annotate(location_has_tags=Exists(Tag.objects.filter(locations=OuterRef("location_id"))))
        .order_by("date", "id")
    )

    if include_domain_info_only:
        first_perf_id_subquery = (
            ActivityLog.objects.filter(location_id=OuterRef("location_id"))
            .order_by("date", "id")
            .values("id")[:1]
        )
        performance_qs = performance_qs.annotate(
            first_perf_id=Subquery(first_perf_id_subquery)
        ).filter(id=F("first_perf_id"))

    if selected_tags:
        performance_qs = performance_qs.filter(
            location_id__in=filter_locations_queryset(
                Location.objects.all(),
                selected_tags=selected_tags,
                domain_terms=domain_terms,
            ).values("id")
        )

    if search_query:
        escaped_search_query = json.dumps(search_query, ensure_ascii=True).strip('"')
        performance_qs = performance_qs.annotate(
            activity_custom_data_text=Cast("custom_data", output_field=TextField()),
            location_custom_data_text=Cast("location__custom_data", output_field=TextField()),
        )
        performance_qs = performance_qs.filter(
            Q(location__name__icontains=search_query)
            | Q(location__tags__name__icontains=search_query)
            | Q(activitylogitem__item__name__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(activity_custom_data_text__icontains=search_query)
            | Q(location_custom_data_text__icontains=search_query)
            | Q(activity_custom_data_text__icontains=escaped_search_query)
            | Q(location_custom_data_text__icontains=escaped_search_query)
        )
    return performance_qs.distinct()


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
        Location.objects.annotate(performance_count=Count("activity_logs", distinct=True))
        .filter(performance_count=0)
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
