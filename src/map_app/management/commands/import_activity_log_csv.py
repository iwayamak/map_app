from django.core.management.base import BaseCommand

from map_app.activity_log_csv_import import import_activity_log_csv

from map_app.models import ActivityItem, ActivityLog, ActivityLogItem, Location


class Command(BaseCommand):
    help = "Import activity log data from CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to CSV file")
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing data before import",
        )

    def handle(self, *args, **options):
        import_activity_log_csv(
            csv_file=options["csv_file"],
            clear_data=options.get("clear", False),
            stdout=self.stdout,
            style=self.style,
            activity_item_model=ActivityItem,
            activity_log_model=ActivityLog,
            activity_log_item_model=ActivityLogItem,
            location_model=Location,
        )
