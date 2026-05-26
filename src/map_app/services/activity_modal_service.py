from django.db.models import Prefetch, Q
from django.db.utils import OperationalError, ProgrammingError
from django.shortcuts import get_object_or_404

from map_app.domain import (
    get_activity_log_item_model,
    get_activity_log_model,
    get_default_domain_terms_func,
    get_domain_field_definition_model,
    get_location_model,
    get_location_photo_model,
    get_site_settings_model,
    get_tag_model,
)
from map_app.domain_terms import get_domain_term_bool
from map_app.services.link_preview_service import build_link_preview_map


def _build_custom_fields_payload(target, custom_data):
    DomainFieldDefinition = get_domain_field_definition_model()
    data = custom_data if isinstance(custom_data, dict) else {}
    definitions = DomainFieldDefinition.objects.filter(
        target=target,
        is_active=True,
    ).order_by("order", "id")

    payload = []
    for definition in definitions:
        raw_value = data.get(definition.key)
        if raw_value in (None, "", []):
            continue

        if isinstance(raw_value, list):
            display_value = ", ".join([str(v) for v in raw_value if str(v).strip()])
        elif isinstance(raw_value, bool):
            display_value = "はい" if raw_value else "いいえ"
        else:
            display_value = str(raw_value)

        if not display_value.strip():
            continue
        payload.append(
            {
                "key": definition.key,
                "label": definition.label,
                "value": display_value,
            }
        )
    return payload


def _build_common_modal_payload(
    *,
    record_id,
    location,
    date,
    current_count,
    activity_items=None,
    songs=None,
    build_link_preview_map_func=build_link_preview_map,
):
    if activity_items is None:
        activity_items = songs or []
    DomainFieldDefinition = get_domain_field_definition_model()
    location_prefetched = getattr(location, "_prefetched_objects_cache", {})
    prefetched_photos = location_prefetched.get("photos")
    prefetched_tags = location_prefetched.get("tags")
    if prefetched_photos is not None:
        location_photos = list(prefetched_photos)
    else:
        location_photos = list(location.photos.only("id", "location_id", "image", "order").order_by("order", "id"))
    if prefetched_tags is not None:
        location_tags = list(prefetched_tags)
    else:
        location_tags = list(location.tags.only("id", "name", "color").order_by("order", "name"))

    photo_assets = []
    for photo in location_photos:
        if not photo.image:
            continue
        full_url = photo.image.url
        try:
            photo.ensure_thumbnails()
            thumb_url = photo.thumbnail_small.url if photo.thumbnail_small else full_url
            medium_url = photo.thumbnail_medium.url if photo.thumbnail_medium else full_url
        except (ProgrammingError, OperationalError, AttributeError):
            thumb_url = full_url
            medium_url = full_url

        photo_assets.append({"thumb_url": thumb_url, "medium_url": medium_url, "full_url": full_url})

    is_new = current_count == 1
    detail_note = location.detail_note
    return {
        "id": record_id,
        "location_name": location.name,
        "date": date.strftime("%Y年%m月%d日"),
        "nearest_station": location.nearest_station,
        "walking_minutes": location.walking_minutes,
        "playable_schedule_note": location.playable_schedule_note,
        "detail_note": detail_note,
        "detail_note_link_previews": build_link_preview_map_func(detail_note),
        "current_count": current_count,
        "badge_color": "#ef4444" if is_new else "#3b82f6",
        "status_badge": "新規" if is_new else "再訪",
        "tags": [
            {"name": tag.name, "color": tag.color, "text_color": tag.text_color}
            for tag in location_tags
        ],
        "activity_items": activity_items,
        "songs": activity_items,
        "custom_fields": _build_custom_fields_payload(
            DomainFieldDefinition.TARGET_LOCATION,
            location.custom_data,
        ),
        "photo_assets": photo_assets,
        "legacy_image_url": location.image.url if location.image and not photo_assets else "",
    }


def build_activity_modal_payload(activity_id, *, build_link_preview_map_func=build_link_preview_map):
    ActivityLog = get_activity_log_model()
    ActivityLogItem = get_activity_log_item_model()
    LocationPhoto = get_location_photo_model()
    Tag = get_tag_model()
    DomainFieldDefinition = get_domain_field_definition_model()
    SiteSettings = get_site_settings_model()
    default_terms = get_default_domain_terms_func()()
    site_settings = SiteSettings.load()
    domain_terms = site_settings.get_domain_terms() if site_settings else default_terms
    use_record_items = get_domain_term_bool(domain_terms, "use_record_items", default=True)

    prefetches = [
        Prefetch(
            "location__photos",
            queryset=LocationPhoto.objects.only("id", "location_id", "image", "order").order_by("order", "id"),
        ),
        Prefetch(
            "location__tags",
            queryset=Tag.objects.only("id", "name", "color").order_by("order", "name"),
        ),
    ]
    if use_record_items:
        prefetches.insert(
            0,
            Prefetch(
                "activitylogitem_set",
                queryset=ActivityLogItem.objects.select_related("item").order_by("order"),
            ),
        )
    activity = get_object_or_404(
        ActivityLog.objects.select_related("location").prefetch_related(*prefetches),
        pk=activity_id,
    )

    current_count = (
        ActivityLog.objects.filter(location_id=activity.location_id)
        .filter(Q(date__lt=activity.date) | Q(date=activity.date, id__lte=activity.id))
        .count()
    )

    activity_items = []
    if use_record_items:
        prefetched = getattr(activity, "_prefetched_objects_cache", {})
        prefetched_items = prefetched.get("activitylogitem_set")
        if prefetched_items is not None:
            activity_log_items = list(prefetched_items)
        else:
            activity_log_items = list(
                ActivityLogItem.objects.filter(activity_log=activity).select_related("item").order_by("order")
            )
        activity_items = [activity_log_item.item.name for activity_log_item in activity_log_items]
        if not activity_items:
            activity_items = activity.title.split(", ") if activity.title else []
    payload = _build_common_modal_payload(
        record_id=activity.id,
        location=activity.location,
        date=activity.date,
        current_count=current_count,
        activity_items=activity_items,
        build_link_preview_map_func=build_link_preview_map_func,
    )
    payload["custom_fields"] = (
        payload["custom_fields"]
        + _build_custom_fields_payload(
            DomainFieldDefinition.TARGET_ACTIVITY_LOG,
            activity.custom_data,
        )
    )
    return payload


def build_performance_modal_payload(performance_id, *, build_link_preview_map_func=build_link_preview_map):
    return build_activity_modal_payload(
        performance_id,
        build_link_preview_map_func=build_link_preview_map_func,
    )


def build_location_modal_payload(location_id, *, build_link_preview_map_func=build_link_preview_map):
    Location = get_location_model()
    LocationPhoto = get_location_photo_model()
    Tag = get_tag_model()
    DomainFieldDefinition = get_domain_field_definition_model()
    location = get_object_or_404(
        Location.objects.prefetch_related(
            Prefetch(
                "photos",
                queryset=LocationPhoto.objects.only("id", "location_id", "image", "order").order_by("order", "id"),
            ),
            Prefetch(
                "tags",
                queryset=Tag.objects.only("id", "name", "color").order_by("order", "name"),
            ),
        ),
        pk=location_id,
    )

    location_prefetched = getattr(location, "_prefetched_objects_cache", {})
    prefetched_photos = location_prefetched.get("photos")
    prefetched_tags = location_prefetched.get("tags")
    if prefetched_photos is not None:
        location_photos = list(prefetched_photos)
    else:
        location_photos = list(location.photos.only("id", "location_id", "image", "order").order_by("order", "id"))
    if prefetched_tags is not None:
        location_tags = list(prefetched_tags)
    else:
        location_tags = list(location.tags.only("id", "name", "color").order_by("order", "name"))

    photo_assets = []
    for photo in location_photos:
        if not photo.image:
            continue
        full_url = photo.image.url
        try:
            photo.ensure_thumbnails()
            thumb_url = photo.thumbnail_small.url if photo.thumbnail_small else full_url
            medium_url = photo.thumbnail_medium.url if photo.thumbnail_medium else full_url
        except (ProgrammingError, OperationalError, AttributeError):
            thumb_url = full_url
            medium_url = full_url
        photo_assets.append({"thumb_url": thumb_url, "medium_url": medium_url, "full_url": full_url})

    detail_note = location.detail_note
    return {
        "id": f"location-{location.id}",
        "location_name": location.name,
        "date": "未訪問",
        "nearest_station": location.nearest_station,
        "walking_minutes": location.walking_minutes,
        "playable_schedule_note": location.playable_schedule_note,
        "detail_note": detail_note,
        "detail_note_link_previews": build_link_preview_map_func(detail_note),
        "current_count": 0,
        "badge_color": "#eab308",
        "status_badge": "未訪問",
        "tags": [
            {"name": tag.name, "color": tag.color, "text_color": tag.text_color}
            for tag in location_tags
        ],
        "activity_items": [],
        "songs": [],
        "custom_fields": _build_custom_fields_payload(
            DomainFieldDefinition.TARGET_LOCATION,
            location.custom_data,
        ),
        "photo_assets": photo_assets,
        "legacy_image_url": location.image.url if location.image and not photo_assets else "",
    }
