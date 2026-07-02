from __future__ import annotations

from datetime import datetime, time

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from map_app.domain import get_activity_log_model
from map_app.services.site_context_service import load_site_context


def build_recent_activity_payload(request, *, limit=5):
    site_settings, _domain_terms = load_site_context()
    ActivityLog = get_activity_log_model()
    activity_logs = (
        ActivityLog.objects.select_related("location")
        .order_by("-date", "-created_at")[:limit]
    )
    map_url = request.build_absolute_uri(reverse(f"{getattr(settings, 'MAP_APP_URL_NAMESPACE', 'map_app')}:map"))
    activities = [_serialize_activity_log(activity_log, map_url) for activity_log in activity_logs]
    return {
        "service": site_settings.site_title,
        "activities": activities,
    }


def _serialize_activity_log(activity_log, map_url):
    record_date = activity_log.date
    location = activity_log.location
    title = activity_log.title or location.name
    summary = f"{location.name} / {record_date.strftime('%Y/%m/%d')}"
    published_at = datetime.combine(record_date, time.min)
    published_at = timezone.make_aware(published_at, timezone.get_current_timezone())
    return {
        "id": f"activity-log:{activity_log.id}",
        "title": title,
        "summary": summary,
        "url": map_url,
        "published_at": published_at.isoformat(),
        "activity_date": record_date.isoformat(),
        "created_at": activity_log.created_at.isoformat(),
        "location": {
            "id": location.id,
            "name": location.name,
        },
    }
