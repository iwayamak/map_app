from datetime import date
from types import SimpleNamespace
from unittest import TestCase

from django.core.exceptions import ValidationError

from map_app.model_behaviors import (
    ActivityLogBehavior,
    DomainFieldDefinitionBehavior,
    SiteSettingsBehavior,
    TagBehavior,
    VideoBehavior,
)


def default_domain_terms():
    return {
        "use_record_items": True,
        "show_video_library_menu": "off",
        "statistics_show_recent_item_title": "yes",
        "modal_sections": {"records": True},
    }


class SiteSettingsStub(SiteSettingsBehavior):
    domain_terms = {"use_record_items": "false", "modal_sections": {"photos": False}}


class TagStub(TagBehavior):
    color = "#ffffff"


class ActivityLogStub(ActivityLogBehavior):
    title = "fallback"

    def __init__(self):
        self._prefetched_objects_cache = {
            "activitylogitem_set": [
                SimpleNamespace(item=SimpleNamespace(name="Item A")),
                SimpleNamespace(item=SimpleNamespace(name="Item B")),
            ]
        }


class DomainFieldDefinitionStub(DomainFieldDefinitionBehavior):
    TYPE_SELECT = "select"
    TYPE_MULTISELECT = "multiselect"
    TYPE_TEXT = "text"

    def __init__(self, key=" Extra_Key ", field_type=TYPE_TEXT, choices_json=None):
        self.key = key
        self.field_type = field_type
        self.choices_json = [] if choices_json is None else choices_json


class VideoStub(VideoBehavior):
    PROCESSING_PENDING = "pending"
    PROCESSING_RUNNING = "running"
    PROCESSING_READY = "ready"
    PROCESSING_FAILED = "failed"

    def __init__(self):
        self.processing_status = self.PROCESSING_PENDING
        self.processing_step = ""
        self.processing_progress_percent = 0
        self.processing_error = "old"
        self.thumbnail_regeneration_requested = True
        self.processed_at = None
        self.thumbnail = None
        self.video_width = 720
        self.video_height = 1280
        self.video_file = SimpleNamespace(size=1536)


class ModelBehaviorTests(TestCase):
    def test_site_settings_domain_terms_are_normalized(self):
        terms = SiteSettingsStub().get_domain_terms()

        self.assertFalse(terms["use_record_items"])
        self.assertFalse(terms["show_video_library_menu"])
        self.assertTrue(terms["statistics_show_recent_item_title"])
        self.assertFalse(terms["modal_sections"]["records"])
        self.assertFalse(terms["modal_sections"]["photos"])

    def test_tag_color_helpers(self):
        self.assertEqual(TagStub().text_color, "#111827")
        self.assertEqual(TagStub._hex_to_rgb_tuple("#0f766e"), (15, 118, 110))
        self.assertRegex(TagStub._build_color_candidate("seed"), r"^#[0-9a-f]{6}$")

    def test_activity_log_uses_prefetched_items(self):
        self.assertEqual(ActivityLogStub().get_item_names(), "Item A, Item B")

    def test_domain_field_definition_validation(self):
        definition = DomainFieldDefinitionStub(key=" Field_1 ")
        definition.clean()
        self.assertEqual(definition.key, "field_1")

        with self.assertRaises(ValidationError):
            DomainFieldDefinitionStub(key="1_invalid").clean()

        with self.assertRaises(ValidationError):
            DomainFieldDefinitionStub(field_type="select", choices_json=[""]).clean()

    def test_video_state_helpers(self):
        video = VideoStub()

        self.assertTrue(video.is_processing_pending)
        self.assertTrue(video.is_portrait_video)
        self.assertEqual(video.video_orientation_class, "is-portrait")
        self.assertEqual(video.video_file_size_display, "1.5 KB")

        video.mark_processing_ready()

        self.assertTrue(video.is_processing_ready)
        self.assertEqual(video.processing_step, "ready")
        self.assertEqual(video.processing_progress_percent, 100)
        self.assertFalse(video.thumbnail_regeneration_requested)
        self.assertGreaterEqual(video.processed_at.date(), date.today())
