import logging
import json
import time
from contextlib import contextmanager
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
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
    backend = (getattr(settings, "VIDEO_PROCESSING_BACKEND", "local") or "local").strip().lower()
    if backend == "sqs":
        return enqueue_video_processing_message(video_id)
    if backend == "both":
        enqueue_video_processing_message(video_id)
        cache.set(VIDEO_PROCESSING_WAKE_KEY, str(video_id), timeout=60)
        return True
    cache.set(VIDEO_PROCESSING_WAKE_KEY, str(video_id), timeout=60)
    return True


def enqueue_video_processing_message(video_id):
    queue_url = (getattr(settings, "VIDEO_PROCESSING_QUEUE_URL", "") or "").strip()
    if not queue_url:
        logger.error("VIDEO_PROCESSING_QUEUE_URL is required when VIDEO_PROCESSING_BACKEND=sqs")
        return False

    video = get_processable_video(video_id)
    if not video or not video.video_file:
        logger.warning("video enqueue skipped because video is missing or has no file. video_id=%s", video_id)
        return False

    try:
        import boto3
    except ImportError:
        logger.exception("boto3 is required for SQS video processing")
        return False

    payload = build_video_processing_payload(video)
    client_kwargs = {"region_name": getattr(settings, "AWS_S3_REGION_NAME", None)}
    access_key_id = (getattr(settings, "SQS_ACCESS_KEY_ID", "") or "").strip()
    secret_access_key = (getattr(settings, "SQS_SECRET_ACCESS_KEY", "") or "").strip()
    if access_key_id and secret_access_key:
        client_kwargs["aws_access_key_id"] = access_key_id
        client_kwargs["aws_secret_access_key"] = secret_access_key
    endpoint_url = getattr(settings, "AWS_SQS_ENDPOINT_URL", "") or ""
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url
    client = boto3.client("sqs", **{key: value for key, value in client_kwargs.items() if value})
    client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(payload, separators=(",", ":")))
    logger.info("video processing message enqueued. video_id=%s queue_url=%s", video_id, queue_url)
    return True


def build_video_processing_payload(video):
    return {
        "video_id": video.pk,
        "input_key": video.video_file.name,
        "title": video.title,
        "thumbnail_only": bool(getattr(video, "thumbnail_regeneration_requested", False)),
        "storage": {
            "bucket": getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""),
            "region": getattr(settings, "AWS_S3_REGION_NAME", "ap-northeast-1"),
            "media_location": getattr(settings, "AWS_MEDIA_LOCATION", "media"),
            "endpoint_url": getattr(settings, "AWS_S3_ENDPOINT_URL", "") or "",
        },
        "callback": {
            "url": getattr(settings, "VIDEO_PROCESSING_CALLBACK_URL", ""),
        },
    }


def update_video_processing_progress(video_id, *, step=None, percent=None):
    Video = get_video_model()
    update_fields = {"updated_at": timezone.now()}
    if step is not None:
        update_fields["processing_step"] = step
    if percent is not None:
        update_fields["processing_progress_percent"] = max(0, min(100, int(percent)))
    Video.objects.filter(pk=video_id).update(**update_fields)


def process_video_now(
    video_id,
    *,
    delete_replaced_file_func=delete_replaced_file,
    get_uploaded_media_dimensions_func=get_uploaded_media_dimensions,
    generate_video_thumbnail_func=generate_video_thumbnail,
    compress_uploaded_video_func=compress_uploaded_video,
    populate_video_dimensions_func=None,
):
    if not getattr(settings, "VIDEO_PROCESSING_ALLOWED", True):
        logger.warning("video processing skipped on disabled host. video_id=%s", video_id)
        return False

    video = get_processable_video(video_id)
    if not video:
        return False

    thumbnail_only = bool(getattr(video, "thumbnail_regeneration_requested", False))
    if populate_video_dimensions_func is None:
        populate_video_dimensions_func = populate_video_dimensions
    previous_video_name = video.video_file.name
    previous_thumbnail_name = video.thumbnail.name if video.thumbnail else None

    try:
        with video_processing_session(video):
            if thumbnail_only:
                populate_video_dimensions_func(video, get_uploaded_media_dimensions_func=get_uploaded_media_dimensions_func)
                update_video_processing_progress(video_id, step="thumbnail", percent=90)
                thumbnail_name, thumbnail_file = generate_video_thumbnail_func(video.video_file, video.title)
                video.thumbnail.save(thumbnail_name, thumbnail_file, save=False)
            else:
                update_video_processing_progress(video_id, step="transcoding", percent=1)
                if should_transcode_video(video):
                    compressed_name, compressed_file, media_metadata = compress_uploaded_video_func(
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
                    populate_video_dimensions_func(video, get_uploaded_media_dimensions_func=get_uploaded_media_dimensions_func)
                    update_video_processing_progress(video_id, step="transcoding", percent=94)

                update_video_processing_progress(video_id, step="thumbnail", percent=95)
                if settings.VIDEO_AUTO_THUMBNAIL_ENABLED and not video.thumbnail:
                    thumbnail_name, thumbnail_file = generate_video_thumbnail_func(video.video_file, video.title)
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

    delete_replaced_file_func(video.video_file, previous_video_name)
    delete_replaced_file_func(video.thumbnail, previous_thumbnail_name)
    return True


def regenerate_video_thumbnail_now(
    video_id,
    *,
    delete_replaced_file_func=delete_replaced_file,
    generate_video_thumbnail_func=generate_video_thumbnail,
):
    video = get_processable_video(video_id)
    if not video:
        return False

    previous_thumbnail_name = video.thumbnail.name if video.thumbnail else None
    try:
        with video_processing_session(video):
            thumbnail_name, thumbnail_file = generate_video_thumbnail_func(video.video_file, video.title)
            video.thumbnail.save(thumbnail_name, thumbnail_file, save=False)
            video.prepare_thumbnail_regeneration()
            video.save(update_fields=["thumbnail", "processing_error", "updated_at"])
    except Exception as exc:
        return handle_thumbnail_exception(video, exc, video_id=video_id)
    finally:
        close_old_connections()

    delete_replaced_file_func(video.thumbnail, previous_thumbnail_name)
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


def populate_video_dimensions(video, *, get_uploaded_media_dimensions_func=get_uploaded_media_dimensions):
    width = int(getattr(video, "video_width", 0) or 0)
    height = int(getattr(video, "video_height", 0) or 0)
    if width > 0 and height > 0:
        return
    detected_width, detected_height = get_uploaded_media_dimensions_func(video.video_file)
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


def apply_video_processing_callback(payload):
    video_id = int(payload.get("video_id") or 0)
    status = (payload.get("status") or "").strip().lower()
    Video = get_video_model()
    video = Video.objects.filter(pk=video_id).first()
    if not video:
        return False, "video not found"

    video._skip_video_processing = True
    previous_video_name = video.video_file.name if video.video_file else ""
    previous_thumbnail_name = video.thumbnail.name if video.thumbnail else ""

    if status == "completed":
        output_key = (payload.get("output_key") or previous_video_name or "").strip()
        thumbnail_key = (payload.get("thumbnail_key") or "").strip()
        if output_key:
            video.video_file.name = output_key
        if thumbnail_key:
            video.thumbnail.name = thumbnail_key
        width = payload.get("video_width")
        height = payload.get("video_height")
        if width:
            video.video_width = int(width)
        if height:
            video.video_height = int(height)
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
        cleanup_processed_input_files(video, previous_video_name, previous_thumbnail_name)
        return True, ""

    error_message = (payload.get("error") or "video processing failed")[:500]
    video.mark_processing_failed(error_message)
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
    return True, ""


def cleanup_processed_input_files(video, previous_video_name, previous_thumbnail_name):
    if previous_video_name and previous_video_name != video.video_file.name:
        default_storage.delete(previous_video_name)
    if previous_thumbnail_name and video.thumbnail and previous_thumbnail_name != video.thumbnail.name:
        default_storage.delete(previous_thumbnail_name)
