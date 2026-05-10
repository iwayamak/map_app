import tempfile
from pathlib import Path

from django.conf import settings

from .ffmpeg import get_ffmpeg_binary, get_media_dimensions, get_media_duration_seconds, run_ffmpeg_command
from .files import build_content_file_from_path, build_generated_media_name, write_uploaded_file


def resolve_transcode_profile(uploaded_file):
    size_bytes = getattr(uploaded_file, "size", 0) or 0
    huge_file_above_mb = max(0, int(getattr(settings, "VIDEO_TRANSCODE_HUGE_FILE_ABOVE_MB", 0) or 0))
    if huge_file_above_mb > 0 and size_bytes >= huge_file_above_mb * 1024 * 1024:
        return {
            "max_width": settings.VIDEO_TRANSCODE_HUGE_MAX_WIDTH,
            "max_fps": settings.VIDEO_TRANSCODE_HUGE_MAX_FPS,
            "crf": settings.VIDEO_TRANSCODE_HUGE_CRF,
            "preset": settings.VIDEO_TRANSCODE_HUGE_PRESET,
            "audio_bitrate": settings.VIDEO_TRANSCODE_HUGE_AUDIO_BITRATE,
        }

    large_file_above_mb = max(0, int(getattr(settings, "VIDEO_TRANSCODE_LARGE_FILE_ABOVE_MB", 0) or 0))
    if large_file_above_mb > 0 and size_bytes >= large_file_above_mb * 1024 * 1024:
        return {
            "max_width": settings.VIDEO_TRANSCODE_LARGE_MAX_WIDTH,
            "max_fps": settings.VIDEO_TRANSCODE_LARGE_MAX_FPS,
            "crf": settings.VIDEO_TRANSCODE_LARGE_CRF,
            "preset": settings.VIDEO_TRANSCODE_LARGE_PRESET,
            "audio_bitrate": settings.VIDEO_TRANSCODE_LARGE_AUDIO_BITRATE,
        }
    return {
        "max_width": settings.VIDEO_TRANSCODE_MAX_WIDTH,
        "max_fps": settings.VIDEO_TRANSCODE_MAX_FPS,
        "crf": settings.VIDEO_TRANSCODE_CRF,
        "preset": settings.VIDEO_TRANSCODE_PRESET,
        "audio_bitrate": settings.VIDEO_TRANSCODE_AUDIO_BITRATE,
    }


def compress_uploaded_video(
    uploaded_file,
    *,
    progress_callback=None,
    get_ffmpeg_binary_func=get_ffmpeg_binary,
    get_media_dimensions_func=get_media_dimensions,
    get_media_duration_seconds_func=get_media_duration_seconds,
    run_ffmpeg_command_func=run_ffmpeg_command,
    build_content_file_from_path_func=build_content_file_from_path,
    build_generated_media_name_func=build_generated_media_name,
    write_uploaded_file_func=write_uploaded_file,
):
    original_name = getattr(uploaded_file, "name", "") or "video"
    input_suffix = Path(original_name).suffix or ".mp4"
    output_name = build_generated_media_name_func("video", ".mp4")

    with tempfile.TemporaryDirectory(prefix="map-app-video-") as temp_dir:
        temp_dir_path = Path(temp_dir)
        input_path = temp_dir_path / f"input{input_suffix}"
        encoded_path = temp_dir_path / "encoded.mp4"
        output_path = temp_dir_path / "output.mp4"

        write_uploaded_file_func(uploaded_file, input_path)
        duration_seconds = get_media_duration_seconds_func(input_path)
        profile = resolve_transcode_profile(uploaded_file)

        scale_filter = f"scale=w='min({profile['max_width']},iw)':h=-2"
        video_filters = [scale_filter]
        if profile["max_fps"] > 0:
            video_filters.append(f"fps={profile['max_fps']}")

        command = [
            get_ffmpeg_binary_func(),
            "-y",
            "-i",
            str(input_path),
            "-threads",
            "1",
            "-vf",
            ",".join(video_filters),
            "-c:v",
            "libx264",
            "-preset",
            profile["preset"],
            "-crf",
            str(profile["crf"]),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            profile["audio_bitrate"],
            str(encoded_path),
        ]

        def ffmpeg_progress_callback(progress_payload):
            if not progress_callback or duration_seconds <= 0:
                return
            try:
                out_time_ms = int(progress_payload.get("out_time_ms") or 0)
            except (TypeError, ValueError):
                return
            if out_time_ms <= 0:
                return
            progress_ratio = min(1.0, out_time_ms / (duration_seconds * 1_000_000))
            progress_callback(int(progress_ratio * 100))

        run_ffmpeg_command_func(command, "動画圧縮に失敗しました。", progress_callback=ffmpeg_progress_callback)
        run_ffmpeg_command_func(
            [
                get_ffmpeg_binary_func(),
                "-y",
                "-i",
                str(encoded_path),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
            "圧縮後の最適化に失敗しました。",
        )
        width, height = get_media_dimensions_func(output_path)
        return output_name, build_content_file_from_path_func(output_path), {"width": width, "height": height}
