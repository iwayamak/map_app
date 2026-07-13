from unittest import TestCase
from unittest.mock import patch

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["map_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        SECRET_KEY="test",
    )
    django.setup()

from map_app import base_models


class BaseModelsTests(TestCase):
    def test_all_base_models_are_abstract(self):
        model_names = [
            "BaseSiteSettings",
            "BaseTag",
            "BaseLocation",
            "BaseLocationPhoto",
            "BaseActivityItem",
            "BaseActivityLog",
            "BaseActivityLogItem",
            "BaseDomainFieldDefinition",
            "BaseVideo",
        ]
        for name in model_names:
            model = getattr(base_models, name)
            self.assertTrue(model._meta.abstract, name)

    def test_activity_log_time_default_uses_current_local_time(self):
        with patch("map_app.base_models.timezone.localtime") as mock_localtime:
            mock_localtime.return_value.replace.return_value.time.return_value = "12:34:56"

            self.assertEqual(base_models.default_activity_log_time(), "12:34:56")
            mock_localtime.return_value.replace.assert_called_once_with(microsecond=0)
