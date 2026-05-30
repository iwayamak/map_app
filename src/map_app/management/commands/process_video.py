from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from map_app.services.video_transcode_service import process_video_now


class Command(BaseCommand):
    help = "Compress and finalize a video asynchronously."

    def add_arguments(self, parser):
        parser.add_argument("video_id", type=int, help="Video primary key to process.")

    def handle(self, *args, **options):
        if not getattr(settings, "VIDEO_PROCESSING_ALLOWED", True):
            raise CommandError(
                "video processing is disabled on this host "
                "(set VIDEO_PROCESSING_ALLOWED=true only on worker hosts)"
            )
        video_id = int(options["video_id"])
        if not process_video_now(video_id):
            raise CommandError(f"Video processing failed. video_id={video_id}")
        self.stdout.write(self.style.SUCCESS(f"Video processing completed. video_id={video_id}"))
