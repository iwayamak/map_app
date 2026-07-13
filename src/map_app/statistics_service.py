from collections import defaultdict
from datetime import date, datetime, time

from map_app.domain import get_location_model


def _resolve_record_title(record):
    if hasattr(record, "get_item_names"):
        return record.get_item_names() or "記録"
    if hasattr(record, "get_record_item_names"):
        return record.get_record_item_names() or "記録"
    return getattr(record, "title", "") or "記録"


def _sortable_datetime_value(value):
    if value is None:
        return 0.0
    if isinstance(value, datetime):
        try:
            return value.timestamp()
        except (OSError, OverflowError, ValueError):
            return 0.0
    if isinstance(value, date):
        return datetime.combine(value, time.min).timestamp()
    return 0.0


def _recent_visit_sort_key(activity_log):
    record_date = getattr(activity_log, "date", None)
    if isinstance(record_date, date):
        date_value = record_date.toordinal()
    else:
        date_value = 0
    record_time = getattr(activity_log, "time", None)
    if isinstance(record_time, time):
        time_value = (record_time.hour * 3600) + (record_time.minute * 60) + record_time.second
    else:
        time_value = 0
    record_id = getattr(activity_log, "pk", None) or getattr(activity_log, "id", None) or 0
    return (
        date_value,
        time_value,
        _sortable_datetime_value(getattr(activity_log, "created_at", None)),
        int(record_id),
    )


def build_map_statistics(activity_logs):
    total_activity_logs = len(activity_logs)
    location_visit_count = {}
    tagged_location_count = 0
    monthly_counts = defaultdict(int)
    location_counts = defaultdict(int)
    location_info = {}

    for activity_log in activity_logs:
        location = activity_log.location
        location_visit_count[location.id] = location_visit_count.get(location.id, 0) + 1
        monthly_counts[activity_log.date.strftime("%Y-%m")] += 1
        location_counts[location.id] += 1
        if location.id not in location_info:
            location_info[location.id] = {
                "name": location.name,
                "latitude": location.latitude,
                "longitude": location.longitude,
            }

    if location_info:
        location_ids = list(location_info.keys())
        Location = get_location_model()
        through_model = Location.tags.through
        tagged_location_count = (
            through_model.objects.filter(location_id__in=location_ids)
            .values("location_id")
            .distinct()
            .count()
        )

    total_locations = len(location_visit_count)
    new_count = total_locations
    revisit_count = total_activity_logs - new_count

    sorted_months = sorted(monthly_counts.items())
    month_labels = [item[0] for item in sorted_months]
    month_values = [item[1] for item in sorted_months]

    recent_visits = sorted(activity_logs, key=_recent_visit_sort_key, reverse=True)[:10]
    recent_visits_data = [
        {
            "location_name": activity_log.location.name,
            "date": activity_log.date.strftime("%Y/%m/%d"),
            "title": _resolve_record_title(activity_log),
            "latitude": activity_log.location.latitude,
            "longitude": activity_log.location.longitude,
        }
        for activity_log in recent_visits
    ]

    top_locations = sorted(location_counts.items(), key=lambda item: item[1], reverse=True)[:20]
    top_locations_data = [
        {
            "name": location_info[loc_id]["name"],
            "count": count,
            "latitude": location_info[loc_id]["latitude"],
            "longitude": location_info[loc_id]["longitude"],
        }
        for loc_id, count in top_locations
    ]

    return {
        "total_activity_logs": total_activity_logs,
        "total_locations": total_locations,
        "tagged_locations": tagged_location_count,
        "new_count": new_count,
        "revisit_count": revisit_count,
        "month_labels": month_labels,
        "month_values": month_values,
        "recent_visits_data": recent_visits_data,
        "top_locations_data": top_locations_data,
    }
