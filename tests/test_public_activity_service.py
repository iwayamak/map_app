from datetime import date, datetime, time, timezone as datetime_timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        MAP_APP_ACTIVITY_LOG_MODEL="map_app.ActivityLog",
        MAP_APP_URL_NAMESPACE="map_app",
        ROOT_URLCONF=__name__,
        USE_TZ=True,
        TIME_ZONE="Asia/Tokyo",
    )
    django.setup()

from map_app.services.public_activity_service import build_recent_activity_payload


def _activity_log(pk, title, location_name, record_date, created_at, record_time=None):
    return SimpleNamespace(
        id=pk,
        title=title,
        date=record_date,
        time=record_time,
        created_at=created_at,
        location=SimpleNamespace(id=10 + pk, name=location_name),
    )


class PublicActivityServiceTests(TestCase):
    def test_build_recent_activity_payload_serializes_activity_logs(self):
        queryset = MagicMock()
        queryset.select_related.return_value.order_by.return_value.__getitem__.return_value = [
            _activity_log(
                1,
                "駅ピアノ",
                "東京駅",
                date(2026, 7, 1),
                datetime(2026, 7, 1, 12, 0, tzinfo=datetime_timezone.utc),
                time(14, 30),
            )
        ]
        request = SimpleNamespace(build_absolute_uri=lambda path: f"https://example.test{path}")

        with (
            patch("map_app.services.public_activity_service.load_site_context", return_value=(SimpleNamespace(site_title="ピアノマップ"), {})),
            patch("map_app.services.public_activity_service.get_activity_log_model", return_value=SimpleNamespace(objects=queryset)),
            patch("map_app.services.public_activity_service.reverse", return_value="/"),
        ):
            payload = build_recent_activity_payload(request, limit=5)

        self.assertEqual(payload["service"], "ピアノマップ")
        self.assertEqual(payload["activities"][0]["id"], "activity-log:1")
        self.assertEqual(payload["activities"][0]["title"], "駅ピアノ")
        self.assertEqual(payload["activities"][0]["summary"], "東京駅 / 2026/07/01 14:30")
        self.assertEqual(payload["activities"][0]["url"], "https://example.test/?activity_log_id=1")
        self.assertEqual(payload["activities"][0]["activity_date"], "2026-07-01")
        self.assertEqual(payload["activities"][0]["activity_time"], "14:30")
