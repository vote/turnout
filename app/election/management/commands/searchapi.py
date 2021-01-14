from django.core.management.base import BaseCommand

from common import enums
from election.models import StateInformation

from .helpers.wraptext import wraptext


class Command(BaseCommand):
    help = "Search the API fields for a string"
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument("search_str", type=str)

    def handle(self, *args, **options):
        search_str = options["search_str"]
        for info in StateInformation.objects.filter(
            text__contains=search_str,
            field_type__field_format__in=[
                enums.StateFieldFormats.MARKDOWN,
                enums.StateFieldFormats.URL,
            ],
        ):
            self.stdout.write(
                self.style.SQL_TABLE(f"{info.state_id} - {info.field_type.slug}")
            )

            self.stdout.write(wraptext(info.text))
