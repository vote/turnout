from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync USVF LEO data"
    requires_system_checks = False

    def handle(self, *args, **options):
        from official.usvf import sync

        sync()
