from unittest import TestCase

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
