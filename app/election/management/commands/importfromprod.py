import json, requests

from django.core.management.base import BaseCommand

from common import enums
from election.models import State, StateInformation, StateInformationFieldType


class Command(BaseCommand):
    help = "Import state information fields from production API"
    requires_system_checks = False

    def add_arguments(self, parser):
        """Add arguments to the command"""
        parser.add_argument(
            "--api-url",
            nargs=1,
            type=str,
            default="https://api.voteamerica.us/v1",
            help="API to import from",
        )

    def handle(self, *args, **options):
        API_URL = options["api_url"]

        fields = requests.get(f'{API_URL}/fields').json()
        for obj in fields:
            # ensure StateInformationFieldTypes exist and match format
            field, created = StateInformationFieldType.objects.get_or_create(
                slug=obj.get('slug'),
            )
            updated = False
            if field.long_name != obj.get('long_name'):
                field.long_name = obj.get('long_name')
                field.save()
                updated = True
            if not field.field_format or field.field_format.value != obj.get('field_format'):
                # compares enum value, set by name
                field_format_name = obj.get('field_format').upper()
                field.field_format = getattr(enums.StateFieldFormats, field_format_name)
                field.save()
                updated = True

            if created:
                    self.stdout.write(self.style.SUCCESS(f"Created {field}"))
            elif updated:
                self.stdout.write(self.style.SUCCESS(f"Updated {field}"))
            else:
                self.stdout.write(f'Unchanged {field}')


        data = requests.get(f'{API_URL}/states').json()
        for obj in data:
            state_code = obj.get('code')
            state = State.objects.get(code=state_code)
            if not state:
                self.stdout.write(f"Not Found {state_code}")
                continue

            for state_information in obj.get('state_information'):
                info, created = StateInformation.objects.get_or_create(
                    state=state,
                    field_type__slug=state_information.get('field_type')
                )
                updated = False

                if info.text != state_information.get('text'):
                    info.text = state_information.get('text')
                    info.save()
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created {info}"))
                elif updated:
                    self.stdout.write(self.style.SUCCESS(f"Updated {info}"))
                else:
                    self.stdout.write(f'Unchanged {info}')
