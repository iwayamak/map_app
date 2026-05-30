from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


SUPPORTED_OUTPUT_FORMATS = {"WEBP", "JPEG"}


def compress_uploaded_image(uploaded_file, *, max_width, max_height, quality, output_format):
    """
    Compress and resize an uploaded image.

    If Pillow cannot decode the file (e.g. RAW/DNG), return the original file.
    """
    if not uploaded_file:
        return uploaded_file

    normalized_format = (output_format or "WEBP").upper()
    if normalized_format not in SUPPORTED_OUTPUT_FORMATS:
        normalized_format = "WEBP"

    try:
        uploaded_file.seek(0)
    except (AttributeError, OSError, ValueError):
        pass

    try:
        with Image.open(uploaded_file) as image:
            image = ImageOps.exif_transpose(image)
            has_alpha = "A" in image.getbands() or image.mode in ("P", "PA")

            if normalized_format == "JPEG":
                # JPEG does not support transparency.
                if has_alpha:
                    image = image.convert("RGBA")
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                elif image.mode != "RGB":
                    image = image.convert("RGB")
            else:
                # Keep alpha channel for WEBP when available.
                if has_alpha and image.mode != "RGBA":
                    image = image.convert("RGBA")
                elif not has_alpha and image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")

            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            buffer = BytesIO()
            if normalized_format == "JPEG":
                save_kwargs = {
                    "format": "JPEG",
                    "quality": quality,
                    "optimize": True,
                    "progressive": True,
                }
                extension = "jpg"
            else:
                save_kwargs = {
                    "format": "WEBP",
                    "quality": quality,
                    "method": 6,
                }
                extension = "webp"

            image.save(buffer, **save_kwargs)
            buffer.seek(0)

            original_name = Path(getattr(uploaded_file, "name", "upload")).stem
            return ContentFile(buffer.read(), name=f"{original_name}.{extension}")
    except (UnidentifiedImageError, OSError, ValueError):
        return uploaded_file
