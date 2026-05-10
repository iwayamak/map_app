import tempfile
from pathlib import Path

from .ffmpeg import get_media_dimensions
from .files import write_uploaded_file


def get_uploaded_media_dimensions(
    uploaded_file,
    *,
    get_media_dimensions_func=get_media_dimensions,
    write_uploaded_file_func=write_uploaded_file,
):
    original_name = getattr(uploaded_file, "name", "") or "video"
    input_suffix = Path(original_name).suffix or ".mp4"

    with tempfile.TemporaryDirectory(prefix="map-app-video-meta-") as temp_dir:
        input_path = Path(temp_dir) / f"input{input_suffix}"
        write_uploaded_file_func(uploaded_file, input_path)
        return get_media_dimensions_func(input_path)
