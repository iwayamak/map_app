from django.core.management.base import BaseCommand

from map_app.media_cleanup import cleanup_local_media


class Command(BaseCommand):
    help = "Clean local MEDIA_ROOT files under a prefix. Defaults to dry-run."

    def add_arguments(self, parser):
        parser.add_argument("--prefix", default="videos/", help="Target prefix under MEDIA_ROOT. Default: videos/")
        parser.add_argument("--days", type=int, default=None, help="Only target files older than N days.")
        parser.add_argument("--delete", action="store_true", help="Actually delete matched files.")
        parser.add_argument("--dry-run", action="store_true", help="Dry-run mode (default behavior).")
        parser.add_argument("--force-local", action="store_true", help="Allow delete even when DEBUG=False.")

    def handle(self, *args, **options):
        delete = bool(options["delete"])
        summary = cleanup_local_media(
            prefix=options["prefix"],
            days=options["days"],
            delete=delete,
            force_local=bool(options["force_local"]),
        )
        self.stdout.write(
            "scanned={scanned} target={target} protected={protected} candidates={candidates} "
            "candidate_bytes={candidate_bytes}".format(
                scanned=summary.scanned_files,
                target=summary.target_files,
                protected=summary.protected_files,
                candidates=summary.candidate_files,
                candidate_bytes=summary.candidate_size_bytes,
            )
        )
        if delete:
            self.stdout.write(
                self.style.SUCCESS(
                    f"deleted={summary.deleted_files} deleted_bytes={summary.deleted_size_bytes}"
                )
            )
        else:
            self.stdout.write("Dry-run only. Add --delete to remove files.")
