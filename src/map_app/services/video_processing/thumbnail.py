import tempfile
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

from .ffmpeg import get_ffmpeg_binary, run_ffmpeg_command
from .files import build_generated_media_name, build_spooled_content_file, write_uploaded_file


def generate_video_thumbnail(
    uploaded_file,
    title,
    *,
    get_ffmpeg_binary_func=get_ffmpeg_binary,
    run_ffmpeg_command_func=run_ffmpeg_command,
    build_generated_media_name_func=build_generated_media_name,
    build_spooled_content_file_func=build_spooled_content_file,
    write_uploaded_file_func=write_uploaded_file,
):
    original_name = getattr(uploaded_file, "name", "") or "video"
    input_suffix = Path(original_name).suffix or ".mp4"
    output_name = build_generated_media_name_func("video-thumb", ".jpg")

    with tempfile.TemporaryDirectory(prefix="map-app-video-thumb-") as temp_dir:
        temp_dir_path = Path(temp_dir)
        input_path = temp_dir_path / f"input{input_suffix}"
        frame_path = temp_dir_path / "frame.jpg"

        write_uploaded_file_func(uploaded_file, input_path)

        command = [
            get_ffmpeg_binary_func(),
            "-y",
            "-ss",
            "00:00:01",
            "-i",
            str(input_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(frame_path),
        ]

        run_ffmpeg_command_func(command, "サムネイル生成に失敗しました。")
        return output_name, build_thumbnail_file(frame_path, build_spooled_content_file_func=build_spooled_content_file_func)


def build_thumbnail_file(frame_path, *, build_spooled_content_file_func=build_spooled_content_file):
    with Image.open(frame_path) as source_image:
        source_image = source_image.convert("RGB")
        source_width, source_height = source_image.size
        is_portrait = source_height > source_width
        image = build_thumbnail_canvas(source_image, is_portrait=is_portrait)
        return build_spooled_content_file_func(image)


def build_thumbnail_canvas(source_image, *, is_portrait):
    source_width, source_height = source_image.size
    if is_portrait:
        canvas_height = max(1280, source_height)
        canvas_width = max(720, int(canvas_height * 9 / 16))
    else:
        canvas_width = max(1280, source_width)
        canvas_height = max(720, int(canvas_width * 9 / 16))
    canvas_size = (canvas_width, canvas_height)

    background = ImageOps.fit(source_image, canvas_size, method=Image.Resampling.LANCZOS)
    if is_portrait:
        background = background.filter(ImageFilter.GaussianBlur(radius=max(4, canvas_width // 320)))
    background_overlay = Image.new("RGBA", canvas_size, (15, 23, 42, 74 if is_portrait else 38))
    return Image.alpha_composite(background.convert("RGBA"), background_overlay)
