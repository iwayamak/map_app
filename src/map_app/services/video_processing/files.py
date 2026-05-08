import tempfile
from datetime import datetime
from uuid import uuid4


def write_uploaded_file(uploaded_file, destination_path):
    if hasattr(uploaded_file, "open"):
        uploaded_file.open("rb")

    with destination_path.open("wb") as destination:
        if hasattr(uploaded_file, "chunks"):
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        else:
            destination.write(uploaded_file.read())

    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)


def build_generated_media_name(prefix, suffix):
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}-{uuid4().hex[:12]}{suffix}"


def build_content_file_from_path(path):
    from django.core.files.base import ContentFile

    return ContentFile(path.read_bytes())


def build_spooled_content_file(image):
    from django.core.files.base import ContentFile

    buffer = tempfile.SpooledTemporaryFile()
    image.convert("RGB").save(buffer, format="JPEG", quality=86, optimize=True, progressive=True)
    buffer.seek(0)
    return ContentFile(buffer.read())


def delete_replaced_file(file_field, previous_name):
    if previous_name and file_field and previous_name != file_field.name:
        file_field.storage.delete(previous_name)
