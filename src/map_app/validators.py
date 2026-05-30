from pathlib import Path

from django.core.exceptions import ValidationError
from django.conf import settings


RAW_EXTENSIONS = {
    ".dng",
    ".raw",
    ".arw",
    ".cr2",
    ".cr3",
    ".nef",
    ".nrw",
    ".orf",
    ".raf",
    ".rw2",
    ".sr2",
}


def validate_non_raw_image(uploaded_file):
    if not uploaded_file:
        return

    extension = Path(getattr(uploaded_file, "name", "")).suffix.lower()
    if extension in RAW_EXTENSIONS:
        raise ValidationError(
            "RAW画像はアップロードできません。JPEG/PNG/HEICなどの表示用画像を選択してください。"
        )

    content_type = getattr(uploaded_file, "content_type", "") or ""
    normalized_content_type = content_type.lower()
    if "x-adobe-dng" in normalized_content_type or normalized_content_type.endswith("/raw"):
        raise ValidationError(
            "RAW画像はアップロードできません。JPEG/PNG/HEICなどの表示用画像を選択してください。"
        )


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-m4v",
    "video/webm",
}


def validate_video_file(uploaded_file):
    if not uploaded_file:
        return

    extension = Path(getattr(uploaded_file, "name", "")).suffix.lower()
    if extension not in VIDEO_EXTENSIONS:
        raise ValidationError("対応している動画形式は MP4 / MOV / M4V / WEBM です。")

    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type and content_type not in VIDEO_CONTENT_TYPES:
        raise ValidationError("動画ファイル形式が不正です。MP4 / MOV / M4V / WEBM をアップロードしてください。")

    max_mb = int(getattr(settings, "MAX_VIDEO_FILE_SIZE_MB", 0) or 0)
    if max_mb > 0:
        max_bytes = max_mb * 1024 * 1024
        if getattr(uploaded_file, "size", 0) > max_bytes:
            raise ValidationError(f"動画サイズが大きすぎます。{max_mb}MB 以下のファイルを選択してください。")
