from datetime import date, datetime, time, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        MAP_APP_LOCATION_MODEL="map_app.Location",
    )
    django.setup()

from map_app.statistics_service import build_map_statistics


def _activity_log(pk, location_id, location_name, record_date, created_at, record_time=None):
    return SimpleNamespace(
        pk=pk,
        id=pk,
        title=f"record-{pk}",
        date=record_date,
        time=record_time,
        created_at=created_at,
        location=SimpleNamespace(
            id=location_id,
            name=location_name,
            latitude=35.0 + location_id,
            longitude=139.0 + location_id,
        ),
    )


class StatisticsServiceTests(TestCase):
    def test_recent_visits_sort_same_date_by_created_at_desc(self):
        fake_location_model = SimpleNamespace(tags=SimpleNamespace(through=MagicMock()))
        fake_location_model.tags.through.objects.filter.return_value.values.return_value.distinct.return_value.count.return_value = 0
        activity_logs = [
            _activity_log(1, 1, "Old same date", date(2026, 6, 1), datetime(2026, 6, 1, 9, tzinfo=timezone.utc)),
            _activity_log(2, 2, "Newest day", date(2026, 6, 2), datetime(2026, 6, 2, 8, tzinfo=timezone.utc)),
            _activity_log(3, 3, "New same date", date(2026, 6, 1), datetime(2026, 6, 1, 18, tzinfo=timezone.utc)),
        ]

        with patch("map_app.statistics_service.get_location_model", return_value=fake_location_model):
            stats = build_map_statistics(activity_logs)

        self.assertEqual(
            [visit["location_name"] for visit in stats["recent_visits_data"]],
            ["Newest day", "New same date", "Old same date"],
        )

    def test_recent_visits_sort_same_date_by_record_time_desc(self):
        fake_location_model = SimpleNamespace(tags=SimpleNamespace(through=MagicMock()))
        fake_location_model.tags.through.objects.filter.return_value.values.return_value.distinct.return_value.count.return_value = 0
        activity_logs = [
            _activity_log(1, 1, "Morning", date(2026, 6, 1), datetime(2026, 6, 1, 18, tzinfo=timezone.utc), time(9, 0)),
            _activity_log(2, 2, "Evening", date(2026, 6, 1), datetime(2026, 6, 1, 8, tzinfo=timezone.utc), time(18, 0)),
        ]

        with patch("map_app.statistics_service.get_location_model", return_value=fake_location_model):
            stats = build_map_statistics(activity_logs)

        self.assertEqual(
            [visit["location_name"] for visit in stats["recent_visits_data"]],
            ["Evening", "Morning"],
        )
