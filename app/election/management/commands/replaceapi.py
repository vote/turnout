import reversion
from django.core.management.base import BaseCommand

from common import enums
from election.models import StateInformation

from .helpers.wraptext import wraptext


class Command(BaseCommand):
    help = "Find-and-replace in the API"
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument("search_str", type=str)
        parser.add_argument("replace_str", type=str)

        parser.add_argument(
            "--apply", action="store_true", help="Actually apply the changes",
        )

    def handle(self, *args, **options):
        search_str = options["search_str"]
        replace_str = options["replace_str"]
        apply = options["apply"]

        n_occurrences = 0
        n_fields = 0

        for info in StateInformation.objects.filter(
            text__contains=search_str,
            field_type__field_format__in=[
                enums.StateFieldFormats.MARKDOWN,
                enums.StateFieldFormats.URL,
            ],
        ):

            old = info.text
            new = old.replace(search_str, replace_str)

            n_fields += 1
            count = old.count(search_str)
            n_occurrences += count

            self.stdout.write(
                self.style.SQL_TABLE(
                    f"{info.state_id} - {info.field_type.slug} ({count} occurrences)"
                )
            )

            self.stdout.write(self.style.ERROR(f"    === OLD ==="))
            self.stdout.write(wraptext(old, indent=8))

            self.stdout.write(self.style.SUCCESS(f"\n    === NEW ==="))
            self.stdout.write(wraptext(new, indent=8))

            self.stdout.write("")

            if apply:
                with reversion.create_revision():
                    info.text = new
                    info.save()

                    reversion.set_comment(
                        f'Bulk find-replace ("{search_str}" -> "{replace_str}")'
                    )

        self.stdout.write("")
        self.stdout.write("")
        if apply:
            self.stdout.write(
                f"Replaced {n_occurrences} occurrences across {n_fields} fields."
            )
        else:
            self.stdout.write(
                f"Found {n_occurrences} occurrences across {n_fields} fields."
            )
            if n_occurrences > 0:
                self.stdout.write(f"Re-run with --apply to apply changes.")
