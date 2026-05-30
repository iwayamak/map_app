from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from map_app.models import Video


class Command(BaseCommand):
    help = "Delete old failed videos and their stored files. Defaults to dry-run."

    def add_arguments(self, parser):
        parser.add_argument(
            "--older-than-days",
            type=int,
            default=7,
            help="Only target failed videos older than this many days.",
        )
        parser.add_argument(
            "--min-size-mb",
            type=int,
            default=0,
            help="Only target video files at or above this many MB.",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Actually delete matched records and files.",
        )

    def handle(self, *args, **options):
        older_than_days = max(0, int(options["older_than_days"]))
        min_size_bytes = max(0, int(options["min_size_mb"])) * 1024 * 1024
        execute = bool(options["execute"])
        cutoff = timezone.now() - timedelta(days=older_than_days)

        queryset = (
            Video.objects.filter(processing_status=Video.PROCESSING_FAILED, updated_at__lt=cutoff)
            .order_by("updated_at", "id")
        )

        candidates = []
        reclaimable_bytes = 0
        for video in queryset:
            try:
                size_bytes = getattr(video.video_file, "size", 0) or 0
            except (FileNotFoundError, OSError, ValueError):
                size_bytes = 0

            if size_bytes < min_size_bytes:
                continue

            reclaimable_bytes += size_bytes
            candidates.append((video, size_bytes))

        if not candidates:
            self.stdout.write("No failed videos matched the cleanup criteria.")
            return

        for video, size_bytes in candidates:
            size_mb = size_bytes / (1024 * 1024) if size_bytes else 0
            self.stdout.write(
                f"id={video.pk} size_mb={size_mb:.1f} updated_at={video.updated_at.isoformat()} "
                f"file={video.video_file.name!r} thumbnail={getattr(video.thumbnail, 'name', '')!r}"
            )

        self.stdout.write(
            f"Matched {len(candidates)} failed videos, reclaimable about {reclaimable_bytes / (1024 * 1024):.1f} MB."
        )

        if not execute:
            self.stdout.write("Dry-run only. Re-run with --execute to delete files and records.")
            return

        deleted_count = 0
        for video, _size_bytes in candidates:
            video_name = video.video_file.name
            thumbnail_name = video.thumbnail.name if video.thumbnail else ""
            storage = video.video_file.storage
            thumbnail_storage = video.thumbnail.storage if video.thumbnail else storage

            with transaction.atomic():
                video.delete()

            if video_name:
                storage.delete(video_name)
            if thumbnail_name:
                thumbnail_storage.delete(thumbnail_name)
            deleted_count += 1

        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} failed videos and related files."))
