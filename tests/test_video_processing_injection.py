from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

import django
from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, override_settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["map_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        SECRET_KEY="test",
        STATIC_URL="/static/",
        MAP_APP_MAP_ASSETS_MODULE="map_app.map_assets",
    )
    django.setup()
else:
    settings.MAP_APP_MAP_ASSETS_MODULE = getattr(settings, "MAP_APP_MAP_ASSETS_MODULE", "map_app.map_assets")
    settings.STATIC_URL = getattr(settings, "STATIC_URL", "/static/")

from map_app.services.video_processing import ffmpeg
from map_app.services.video_processing import pipeline
from map_app.admin_video import VideoAdmin
from map_app.models import Video


class _DummyFileField:
    def __init__(self, name):
        self.name = name

    def save(self, name, _content, save=False):  # noqa: ARG002
        self.name = name


class VideoProcessingInjectionTests(TestCase):
    def test_run_ffmpeg_command_uses_injected_subprocess_module(self):
        subprocess_module = SimpleNamespace(
            run=MagicMock(return_value=SimpleNamespace(stdout="", stderr="")),
            CalledProcessError=RuntimeError,
            PIPE=object(),
            STDOUT=object(),
        )

        ffmpeg.run_ffmpeg_command(
            ["ffmpeg", "-version"],
            "failed",
            subprocess_module=subprocess_module,
        )

        subprocess_module.run.assert_called_once()

    @patch("map_app.services.video_processing.pipeline.close_old_connections")
    @patch("map_app.services.video_processing.pipeline.update_video_processing_progress")
    @patch("map_app.services.video_processing.pipeline.get_processable_video")
    def test_process_video_now_uses_injected_dependencies_for_thumbnail_only(
        self,
        mock_get_processable_video,
        _mock_update_progress,
        _mock_close_connections,
    ):
        video = SimpleNamespace(
            thumbnail_regeneration_requested=True,
            video_file=_DummyFileField("videos/original.mp4"),
            thumbnail=_DummyFileField("thumbs/old.jpg"),
            title="sample",
            video_width=0,
            video_height=0,
            mark_processing_ready=MagicMock(),
            save=MagicMock(),
        )
        mock_get_processable_video.return_value = video

        populate_video_dimensions_func = MagicMock()
        generate_video_thumbnail_func = MagicMock(return_value=("thumbs/new.jpg", object()))
        delete_replaced_file_func = MagicMock()

        processed = pipeline.process_video_now(
            1,
            populate_video_dimensions_func=populate_video_dimensions_func,
            generate_video_thumbnail_func=generate_video_thumbnail_func,
            delete_replaced_file_func=delete_replaced_file_func,
            compress_uploaded_video_func=MagicMock(),
            get_uploaded_media_dimensions_func=MagicMock(),
        )

        self.assertTrue(processed)
        populate_video_dimensions_func.assert_called_once()
        generate_video_thumbnail_func.assert_called_once()
        delete_replaced_file_func.assert_any_call(video.video_file, "videos/original.mp4")
        delete_replaced_file_func.assert_any_call(video.thumbnail, "thumbs/old.jpg")

    @override_settings(
        AWS_STORAGE_BUCKET_NAME="media-bucket",
        AWS_S3_REGION_NAME="ap-northeast-1",
        AWS_MEDIA_LOCATION="media",
        VIDEO_PROCESSING_CALLBACK_URL="https://example.com/api/video-processing/callback/",
    )
    def test_build_video_processing_payload_uses_relative_storage_keys(self):
        video = SimpleNamespace(
            pk=10,
            video_file=SimpleNamespace(name="videos/direct/input.mp4"),
            title="sample",
            thumbnail_regeneration_requested=False,
        )

        payload = pipeline.build_video_processing_payload(video)

        self.assertEqual(payload["video_id"], 10)
        self.assertEqual(payload["input_key"], "videos/direct/input.mp4")
        self.assertEqual(payload["storage"]["bucket"], "media-bucket")
        self.assertEqual(payload["storage"]["media_location"], "media")
        self.assertEqual(payload["callback"]["url"], "https://example.com/api/video-processing/callback/")

    @override_settings(USE_S3=True, VIDEO_DIRECT_UPLOAD_ENABLED=False)
    @patch("map_app.admin_video.reverse", return_value="/admin/map_app/video/direct-upload-url/")
    def test_video_admin_can_disable_direct_upload(self, _mock_reverse):
        request = RequestFactory().get("/admin/map_app/video/add/")
        video_admin = VideoAdmin(Video, AdminSite())

        formfield = video_admin.formfield_for_dbfield(Video._meta.get_field("video_file"), request)

        self.assertEqual(formfield.widget.attrs["data-direct-upload-enabled"], "0")

    @override_settings(VIDEO_PROCESSING_CALLBACK_SECRET="secret")
    @patch("map_app.video_processing_callback.apply_video_processing_callback")
    def test_video_processing_callback_requires_valid_signature(self, mock_apply_callback):
        import hashlib
        import hmac
        import json

        from map_app.video_processing_callback import video_processing_callback_view

        body = json.dumps({"video_id": 1, "status": "completed"}, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
        mock_apply_callback.return_value = (True, "")

        request = RequestFactory().post(
            "/api/video-processing/callback/",
            data=body,
            content_type="application/json",
            HTTP_X_VIDEO_PROCESSING_SIGNATURE=f"sha256={signature}",
        )
        response = video_processing_callback_view(request)

        self.assertEqual(response.status_code, 200)
        mock_apply_callback.assert_called_once()

    @override_settings(VIDEO_PROCESSING_CALLBACK_SECRET="secret")
    @patch("map_app.video_processing_callback.apply_video_processing_callback")
    def test_video_processing_callback_rejects_invalid_signature(self, mock_apply_callback):
        from map_app.video_processing_callback import video_processing_callback_view

        request = RequestFactory().post(
            "/api/video-processing/callback/",
            data=b'{"video_id":1}',
            content_type="application/json",
            HTTP_X_VIDEO_PROCESSING_SIGNATURE="sha256=invalid",
        )
        response = video_processing_callback_view(request)

        self.assertEqual(response.status_code, 403)
        mock_apply_callback.assert_not_called()


class ServiceInjectionTests(TestCase):
    def test_healthcheck_uses_injected_cache_and_connection(self):
        from map_app.services.healthcheck_service import run_health_checks

        class _FakeCache:
            def __init__(self):
                self.set = MagicMock()
                self.get = MagicMock(return_value="ok")
                self._cache = SimpleNamespace(get_client=lambda: SimpleNamespace(ping=lambda: True))

        fake_cache = _FakeCache()
        fake_cursor = MagicMock()
        fake_cursor.__enter__.return_value = fake_cursor
        fake_connection = SimpleNamespace(cursor=MagicMock(return_value=fake_cursor))

        result = run_health_checks(cache_backend=fake_cache, db_connection=fake_connection)
        self.assertEqual(result["status"], "ok")
        fake_connection.cursor.assert_called_once()
        fake_cache.set.assert_called_once()

    def test_activity_modal_uses_injected_link_preview_builder(self):
        from map_app.services.activity_modal_service import _build_common_modal_payload

        location = SimpleNamespace(
            name="loc",
            nearest_station="st",
            walking_minutes=1,
            playable_schedule_note="",
            detail_note="note",
            custom_data={},
            image=None,
            photos=MagicMock(),
            tags=MagicMock(),
        )
        location.photos.only.return_value.order_by.return_value = []
        location.tags.only.return_value.order_by.return_value = []
        build_link_preview_map_func = MagicMock(return_value={"k": "v"})

        with patch("map_app.services.activity_modal_service.get_domain_field_definition_model") as mock_model:
            mock_manager = MagicMock()
            mock_manager.filter.return_value.order_by.return_value = []
            mock_model.return_value = SimpleNamespace(
                TARGET_LOCATION="location",
                objects=mock_manager,
            )
            payload = _build_common_modal_payload(
                record_id=1,
                location=location,
                date=SimpleNamespace(strftime=lambda _fmt: "2026-01-01"),
                current_count=1,
                activity_items=[],
                build_link_preview_map_func=build_link_preview_map_func,
            )

        self.assertEqual(payload["detail_note_link_previews"], {"k": "v"})
        build_link_preview_map_func.assert_called_once_with("note")
