from django.core.management.base import BaseCommand

from absentee.region_links import refresh_region_links


class Command(BaseCommand):
    help = "Scrap OVBM per-region links"
    requires_system_checks = False

    def handle(self, *args, **options):
        refresh_region_links()
        print("Done.")
