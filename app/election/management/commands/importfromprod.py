import requests
from django.core.management.base import BaseCommand

from common import enums
from election.models import StateInformation, StateInformationFieldType


class Command(BaseCommand):
    help = "Import state information fields from production API"
    requires_system_checks = False

    def add_arguments(self, parser):
        """Add arguments to the command"""
        parser.add_argument(
            "--api-url",
            nargs=1,
            type=str,
            default=["https://api.voteamerica.com/v1"],
            help="API to import from",
        )

    def handle(self, *args, **options):
        API_URL = options["api_url"][0]

        fields = requests.get(f"{API_URL}/election/field/").json()
        for obj in fields:
            # ensure StateInformationFieldTypes exist and match format
            field, created = StateInformationFieldType.objects.get_or_create(
                slug=obj.get("slug"),
            )
            updated = False
            if field.long_name != obj.get("long_name"):
                field.long_name = obj.get("long_name")
                field.save()
                updated = True
            if not field.field_format or field.field_format.value != obj.get(
                "field_format"
            ):
                # compares enum value, set by name
                obj.get("field_format").upper()
                field.field_format = enums.StateFieldFormats(obj.get("field_format"))
                field.save()
                updated = True

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {field}"))
            elif updated:
                self.stdout.write(self.style.SUCCESS(f"Updated {field}"))
            else:
                self.stdout.write(f"Unchanged {field}")

        data = requests.get(f"{API_URL}/election/state/").json()
        for state in data:
            data_dictionary = dict(
                [(x["field_type"], x["text"]) for x in state["state_information"]]
            )
            # Our custom manager for StateInformation will ensure a select_related() to field_type is done here
            existing_information = StateInformation.objects.filter(
                state__code=state.get("code"),
                field_type__slug__in=data_dictionary.keys(),
            )
            for info in existing_information:
                updated = False
                specific_data = data_dictionary[info.field_type.slug]
                if info.text != specific_data:
                    info.text = specific_data
                    info.save()
                    updated = True

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created {info}"))
                elif updated:
                    self.stdout.write(self.style.SUCCESS(f"Updated {info}"))
                else:
                    self.stdout.write(f"Unchanged {info}")
