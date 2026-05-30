from django.core.management.base import BaseCommand

from map_app.services.map_cache_warmup_service import warm_map_cache_now


class Command(BaseCommand):
    help = 'Warm the map page cache immediately.'

    def add_arguments(self, parser):
        parser.add_argument('--reason', default='manual', help='Reason label for warmup logs.')

    def handle(self, *args, **options):
        reason = (options.get('reason') or 'manual').strip() or 'manual'
        warm_map_cache_now(reason=reason)
        self.stdout.write(self.style.SUCCESS(f'Map cache warmup triggered. reason={reason}'))
