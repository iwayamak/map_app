from types import SimpleNamespace
from unittest import TestCase

import django
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import override_settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
        STATIC_URL="/static/",
        USE_TZ=True,
        MAP_APP_MAP_ASSETS_MODULE="map_app.map_assets",
        MAP_APP_CACHE_KEY_NAMESPACE="test",
        COMPRESS_IMAGES=False,
        IMAGE_MAX_WIDTH=1200,
        IMAGE_MAX_HEIGHT=900,
        IMAGE_QUALITY=82,
        IMAGE_OUTPUT_FORMAT="WEBP",
        VIDEO_TRANSCODE_ENABLED=False,
        VIDEO_AUTO_THUMBNAIL_ENABLED=False,
    )
    django.setup()

from map_app.model_behaviors import (
    ActivityLogBehavior,
    DomainFieldDefinitionBehavior,
    LocationBehavior,
    LocationPhotoBehavior,
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


class SaveRecorder:
    def save(self, *args, **kwargs):
        self.saved_args = args
        self.saved_kwargs = kwargs


class SiteSettingsStub(SiteSettingsBehavior, SaveRecorder):
    domain_terms = {"use_record_items": "false", "modal_sections": {"photos": False}}

    def __init__(self):
        self.pk = None
        self.site_logo = None
        self.favicon = None

    def _compress_uploaded_image(self, image, *, max_width, max_height, quality, output_format):
        return image


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


class LocationStub(LocationBehavior, SaveRecorder):
    def __init__(self):
        self.name = "  東京駅  "
        self.image = SimpleNamespace(name="photo.jpg", _committed=False)

    def _compress_uploaded_image(self, image, *, max_width, max_height, quality, output_format):
        return SimpleNamespace(
            source=image,
            max_width=max_width,
            max_height=max_height,
            quality=quality,
            output_format=output_format,
            _committed=False,
        )


class LocationPhotoStub(LocationPhotoBehavior):
    def __init__(self):
        self.pk = 123
        self.image = SimpleNamespace(name="location_photos/original.jpg", _committed=True)

    def _compress_uploaded_image(self, image, *, max_width, max_height, quality, output_format):
        return SimpleNamespace(
            source=image,
            max_width=max_width,
            max_height=max_height,
            quality=quality,
            output_format=output_format,
            name="",
        )


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
        self.pk = None
        self.is_published = False
        self.published_at = None

    def _schedule_video_processing(self, video_id):
        return None


class ModelBehaviorTests(TestCase):
    def test_site_settings_domain_terms_are_normalized(self):
        terms = SiteSettingsStub().get_domain_terms()

        self.assertFalse(terms["use_record_items"])
        self.assertFalse(terms["show_video_library_menu"])
        self.assertTrue(terms["statistics_show_recent_item_title"])
        self.assertFalse(terms["modal_sections"]["records"])
        self.assertFalse(terms["modal_sections"]["photos"])

    @override_settings(COMPRESS_IMAGES=False)
    def test_site_settings_save_forces_singleton_pk_and_clears_cache(self):
        site_settings = SiteSettingsStub()

        site_settings.save(update_fields=["site_title"])

        self.assertEqual(site_settings.pk, 1)
        self.assertEqual(site_settings.saved_kwargs, {"update_fields": ["site_title"]})

    def test_tag_color_helpers(self):
        self.assertEqual(TagStub().text_color, "#111827")
        self.assertEqual(TagStub._hex_to_rgb_tuple("#0f766e"), (15, 118, 110))
        self.assertRegex(TagStub._build_color_candidate("seed"), r"^#[0-9a-f]{6}$")

    def test_activity_log_uses_prefetched_items(self):
        self.assertEqual(ActivityLogStub().get_item_names(), "Item A, Item B")

    @override_settings(
        COMPRESS_IMAGES=True,
        IMAGE_MAX_WIDTH=1200,
        IMAGE_MAX_HEIGHT=900,
        IMAGE_QUALITY=82,
        IMAGE_OUTPUT_FORMAT="WEBP",
    )
    def test_location_save_trims_name_and_compresses_image(self):
        location = LocationStub()

        location.save()

        self.assertEqual(location.name, "東京駅")
        self.assertEqual(location.image.output_format, "WEBP")
        self.assertEqual(location.image.max_width, 1200)
        self.assertEqual(location.saved_kwargs, {})

    def test_location_photo_builds_thumbnail_file(self):
        photo = LocationPhotoStub()

        thumbnail = photo._build_thumbnail_file(256, 256, 75, "sm")

        self.assertEqual(thumbnail.name, "location_photos/thumbs/original_123_sm.webp")
        self.assertEqual(thumbnail.output_format, "WEBP")
        self.assertEqual(thumbnail.max_width, 256)

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
        self.assertIsNotNone(video.processed_at)

    @override_settings(VIDEO_TRANSCODE_ENABLED=False, VIDEO_AUTO_THUMBNAIL_ENABLED=False)
    def test_video_processing_start_condition_respects_settings(self):
        video = VideoStub()
        video.video_file = SimpleNamespace(name="video.mp4", _committed=False)

        self.assertFalse(video._should_start_video_processing())

        video._force_video_processing = True

        self.assertTrue(video._should_start_video_processing())
