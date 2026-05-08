from django.db.models import Case, F, IntegerField, Value, When

from map_app.domain import get_video_model


def build_video_sort_expression():
    return Case(
        When(featured_order__isnull=True, then=Value(999999)),
        default=F("featured_order"),
        output_field=IntegerField(),
    )


def get_published_videos_queryset():
    Video = get_video_model()
    featured_sort = build_video_sort_expression()
    return (
        Video.objects.filter(is_published=True, processing_status=Video.PROCESSING_READY)
        .exclude(video_file="")
        .order_by("-is_featured", featured_sort, "-published_at", "-created_at")
    )


def build_interleaved_video_rows(source_videos, portrait_row_size, landscape_row_size, include_remainder=True):
    portrait_videos = [video for video in source_videos if video.is_portrait_video]
    landscape_videos = [video for video in source_videos if not video.is_portrait_video]
    rows = []

    def _video_sort_key(video):
        return video.published_at or video.created_at

    while True:
        portrait_ready = len(portrait_videos) >= portrait_row_size
        landscape_ready = len(landscape_videos) >= landscape_row_size
        if not portrait_ready and not landscape_ready:
            break

        portrait_head = _video_sort_key(portrait_videos[0]) if portrait_ready else None
        landscape_head = _video_sort_key(landscape_videos[0]) if landscape_ready else None

        if portrait_ready and (not landscape_ready or portrait_head >= landscape_head):
            rows.append({"orientation": "portrait", "items": portrait_videos[:portrait_row_size]})
            portrait_videos = portrait_videos[portrait_row_size:]
        else:
            rows.append({"orientation": "landscape", "items": landscape_videos[:landscape_row_size]})
            landscape_videos = landscape_videos[landscape_row_size:]

    if include_remainder:
        if portrait_videos:
            rows.append({"orientation": "portrait", "items": portrait_videos})
        if landscape_videos:
            rows.append({"orientation": "landscape", "items": landscape_videos})

    return rows
