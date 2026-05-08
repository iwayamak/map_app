import logging
import time
from contextlib import contextmanager
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import close_old_connections
from django.db import transaction
from django.utils import timezone

from map_app.cache_keys import VIDEO_PROCESSING_WAKE_KEY
from map_app.domain import get_video_model

from .files import delete_replaced_file
from .metadata import get_uploaded_media_dimensions
from .thumbnail import generate_video_thumbnail
from .transcode import compress_uploaded_video

logger = logging.getLogger(__name__)


def schedule_video_processing(video_id):
    cache.set(VIDEO_PROCESSING_WAKE_KEY, str(video_id), timeout=60)
    return True


def update_video_processing_progress(video_id, *, step=None, percent=None):
    Video = get_video_model()
    update_fields = {"updated_at": timezone.now()}
    if step is not None:
        update_fields["processing_step"] = step
    if percent is not None:
        update_fields["processing_progress_percent"] = max(0, min(100, int(percent)))
    Video.objects.filter(pk=video_id).update(**update_fields)


def process_video_now(video_id):
    if not getattr(settings, "VIDEO_PROCESSING_ALLOWED", True):
        logger.warning("video processing skipped on disabled host. video_id=%s", video_id)
        return False

    video = get_processable_video(video_id)
    if not video:
        return False

    thumbnail_only = bool(getattr(video, "thumbnail_regeneration_requested", False))
    previous_video_name = video.video_file.name
    previous_thumbnail_name = video.thumbnail.name if video.thumbnail else None

    try:
        with video_processing_session(video):
            if thumbnail_only:
                populate_video_dimensions(video)
                update_video_processing_progress(video_id, step="thumbnail", percent=90)
                thumbnail_name, thumbnail_file = generate_video_thumbnail(video.video_file, video.title)
                video.thumbnail.save(thumbnail_name, thumbnail_file, save=False)
            else:
                update_video_processing_progress(video_id, step="transcoding", percent=1)
                if should_transcode_video(video):
                    compressed_name, compressed_file, media_metadata = compress_uploaded_video(
                        video.video_file,
                        progress_callback=lambda percent: update_video_processing_progress(
                            video_id,
                            step="transcoding",
                            percent=min(94, max(1, percent)),
                        ),
                    )
                    video.video_file.save(compressed_name, compressed_file, save=False)
                    video.video_width = media_metadata.get("width")
                    video.video_height = media_metadata.get("height")
                else:
                    populate_video_dimensions(video)
                    update_video_processing_progress(video_id, step="transcoding", percent=94)

                update_video_processing_progress(video_id, step="thumbnail", percent=95)
                if settings.VIDEO_AUTO_THUMBNAIL_ENABLED and not video.thumbnail:
                    thumbnail_name, thumbnail_file = generate_video_thumbnail(video.video_file, video.title)
                    video.thumbnail.save(thumbnail_name, thumbnail_file, save=False)

            update_video_processing_progress(video_id, step="finalizing", percent=99)
            video.mark_processing_ready()
            update_fields = [
                "video_file",
                "thumbnail",
                "processing_status",
                "processing_error",
                "processing_step",
                "processing_progress_percent",
                "video_width",
                "video_height",
                "thumbnail_regeneration_requested",
                "processed_at",
                "updated_at",
            ]
            video.save(update_fields=update_fields)
    except Exception as exc:
        return handle_processing_exception(video, exc, video_id=video_id)
    finally:
        close_old_connections()

    delete_replaced_file(video.video_file, previous_video_name)
    delete_replaced_file(video.thumbnail, previous_thumbnail_name)
    return True


def regenerate_video_thumbnail_now(video_id):
    video = get_processable_video(video_id)
    if not video:
        return False

    previous_thumbnail_name = video.thumbnail.name if video.thumbnail else None
    try:
        with video_processing_session(video):
            thumbnail_name, thumbnail_file = generate_video_thumbnail(video.video_file, video.title)
            video.thumbnail.save(thumbnail_name, thumbnail_file, save=False)
            video.prepare_thumbnail_regeneration()
            video.save(update_fields=["thumbnail", "processing_error", "updated_at"])
    except Exception as exc:
        return handle_thumbnail_exception(video, exc, video_id=video_id)
    finally:
        close_old_connections()

    delete_replaced_file(video.thumbnail, previous_thumbnail_name)
    return True


def get_processable_video(video_id):
    Video = get_video_model()
    close_old_connections()
    return Video.objects.filter(pk=video_id).first()


@contextmanager
def video_processing_session(video):
    video._skip_video_processing = True
    try:
        yield video
    finally:
        video._skip_video_processing = False


def handle_processing_exception(video, exc, *, video_id):
    if video is None:
        return False
    if exc.__class__.__name__ != "ValidationError":
        logger.exception("Unexpected video processing error. video_id=%s", video_id)
    video.mark_processing_failed(truncate_error_message(exc))
    video.save(
        update_fields=[
            "processing_status",
            "processing_step",
            "processing_error",
            "processing_progress_percent",
            "thumbnail_regeneration_requested",
            "updated_at",
        ]
    )
    return False


def handle_thumbnail_exception(video, exc, *, video_id):
    if video is None:
        return False
    if exc.__class__.__name__ != "ValidationError":
        logger.exception("Unexpected thumbnail regeneration error. video_id=%s", video_id)
    video.processing_step = "failed"
    video.processing_error = truncate_error_message(exc)
    video.save(update_fields=["processing_step", "processing_error", "updated_at"])
    return False


def truncate_error_message(exc):
    messages = getattr(exc, "messages", None)
    if messages:
        return " ".join(messages)[:500]
    return f"{exc.__class__.__name__}: {str(exc).strip()}"[:500]


def populate_video_dimensions(video):
    width = int(getattr(video, "video_width", 0) or 0)
    height = int(getattr(video, "video_height", 0) or 0)
    if width > 0 and height > 0:
        return
    detected_width, detected_height = get_uploaded_media_dimensions(video.video_file)
    video.video_width = detected_width
    video.video_height = detected_height


def should_transcode_video(video):
    if not getattr(settings, "VIDEO_TRANSCODE_ENABLED", True):
        return False
    skip_above_mb = max(0, int(getattr(settings, "VIDEO_TRANSCODE_SKIP_ABOVE_MB", 0) or 0))
    if skip_above_mb <= 0:
        return True
    try:
        size_bytes = getattr(video.video_file, "size", 0) or 0
    except (FileNotFoundError, OSError, ValueError):
        return True
    skip_limit_bytes = skip_above_mb * 1024 * 1024
    if size_bytes > skip_limit_bytes:
        logger.info("video transcode skipped video_id=%s size_bytes=%s skip_above_mb=%s", video.pk, size_bytes, skip_above_mb)
        return False
    return True


def claim_next_video_for_processing(stale_after_seconds=3600):
    Video = get_video_model()
    close_old_connections()
    stale_cutoff = timezone.now() - timedelta(seconds=max(60, int(stale_after_seconds)))
    candidates = (
        list(Video.objects.filter(processing_status=Video.PROCESSING_PENDING).order_by("created_at", "id").values_list("id", flat=True)[:1])
        + list(
            Video.objects.filter(processing_status=Video.PROCESSING_RUNNING, updated_at__lt=stale_cutoff)
            .order_by("updated_at", "id")
            .values_list("id", flat=True)[:1]
        )
    )
    for video_id in candidates:
        with transaction.atomic():
            updated = (
                Video.objects.filter(pk=video_id, processing_status__in=[Video.PROCESSING_PENDING, Video.PROCESSING_RUNNING])
                .update(
                    processing_status=Video.PROCESSING_RUNNING,
                    processing_step="running",
                    processing_error="",
                    processing_progress_percent=0,
                    updated_at=timezone.now(),
                )
            )
        if updated:
            return video_id
    return None


def wait_for_video_job(poll_interval_seconds=5):
    poll_interval_seconds = max(1, int(poll_interval_seconds))
    if cache.get(VIDEO_PROCESSING_WAKE_KEY):
        cache.delete(VIDEO_PROCESSING_WAKE_KEY)
        return
    time.sleep(poll_interval_seconds)
