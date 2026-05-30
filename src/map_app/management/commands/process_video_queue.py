import fcntl
import os
from contextlib import contextmanager

from django.conf import settings
from django.core.management.base import BaseCommand

from map_app.services.video_transcode_service import process_video_now
from map_app.services.video_processing.pipeline import claim_next_video_for_processing, wait_for_video_job


@contextmanager
def worker_lock(lock_path):
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    with open(lock_path, "w", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        handle.write(str(os.getpid()))
        handle.flush()
        try:
            yield True
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class Command(BaseCommand):
    help = "Process queued videos with a single local worker."

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true", help="Keep polling for queued videos.")
        parser.add_argument(
            "--poll-interval",
            type=int,
            default=5,
            help="Polling interval in seconds while waiting for new jobs.",
        )
        parser.add_argument(
            "--stale-after",
            type=int,
            default=3600,
            help="Reclaim running jobs older than this many seconds.",
        )

    def handle(self, *args, **options):
        if not getattr(settings, "VIDEO_PROCESSING_ALLOWED", True):
            self.stdout.write(
                self.style.ERROR(
                    "video processing is disabled on this host "
                    "(set VIDEO_PROCESSING_ALLOWED=true only on worker hosts)"
                )
            )
            return

        lock_path = os.getenv(
            "VIDEO_WORKER_LOCK_PATH",
            str(getattr(settings, "BASE_DIR")) + "/tmp/video-worker.lock",
        )
        loop = bool(options["loop"])
        poll_interval = max(1, int(options["poll_interval"]))
        stale_after = max(60, int(options["stale_after"]))

        with worker_lock(lock_path) as acquired:
            if not acquired:
                self.stdout.write("video worker already running; exiting")
                return

            while True:
                video_id = claim_next_video_for_processing(stale_after_seconds=stale_after)
                if video_id is None:
                    if not loop:
                        self.stdout.write("no queued videos")
                        return
                    wait_for_video_job(poll_interval_seconds=poll_interval)
                    continue

                self.stdout.write(f"processing video_id={video_id}")
                process_video_now(video_id)
