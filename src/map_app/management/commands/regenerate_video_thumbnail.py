from django.core.management.base import BaseCommand, CommandError

from map_app.services.video_transcode_service import regenerate_video_thumbnail_now


class Command(BaseCommand):
    help = "Regenerate and overwrite a video's thumbnail."

    def add_arguments(self, parser):
        parser.add_argument("video_id", type=int, help="Video primary key to process.")

    def handle(self, *args, **options):
        video_id = int(options["video_id"])
        if not regenerate_video_thumbnail_now(video_id):
            raise CommandError(f"Thumbnail regeneration failed. video_id={video_id}")
        self.stdout.write(
            self.style.SUCCESS(f"Thumbnail regeneration completed. video_id={video_id}")
        )
