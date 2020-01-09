import argparse
import csv

from django.core.management.base import BaseCommand

from election.models import State, StateInformation


def clean_field(text):
    clean_text = text.strip()
    return clean_text


class Command(BaseCommand):
    help = "Import state information"
    requires_system_checks = False

    def add_arguments(self, parser):
        """Add arguments to the command"""
        parser.add_argument(
            "file",
            nargs=1,
            type=argparse.FileType("r", encoding="utf-8", errors="ignore"),
            help="CSV to import",
        )

    def handle(self, *args, **options):
        csv_file = options["file"][0]
        reader = csv.DictReader(csv_file)

        for row in reader:
            state_name = row["State"].replace("-", " ")
            state = State.objects.filter(name__iexact=state_name).first()
            if not state:
                self.stdout.write(f"Not Found {row['State']}")
                continue

            fields = StateInformation.objects.filter(
                field_type__long_name__in=reader.fieldnames, state=state
            )
            for field in fields:
                text = row.get(field.field_type.long_name)
                if text:
                    clean_text = clean_field(text)
                    if clean_text and field.text != clean_text:
                        field.text = clean_text
                        field.save()
                        self.stdout.write(self.style.SUCCESS(f"Updated {field}"))
