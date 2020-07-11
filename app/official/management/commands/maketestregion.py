from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.db import transaction

from official.models import Address, Office, Region

TEST_REGION_ID = 999999999
TEST_OFFICE_ID = 999999998
TEST_ADDRESS_ID = 999999997


class Command(BaseCommand):
    help = "Create or replace a testing region"
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument("state", type=str)

        parser.add_argument(
            "--email",
            type=str,
            default="",
            help="Associate an email address with the region",
        )

        parser.add_argument(
            "--fax", type=str, default="", help="Associate a fax number with the region"
        )

    def handle(self, *args, **options):
        # Delete the existing testing region if there is one
        with transaction.atomic():
            try:
                existing_region = Region.objects.get(external_id=TEST_REGION_ID)
                existing_region.delete()
            except Region.DoesNotExist:
                pass

            # Create a region
            region = Region(
                external_id=TEST_REGION_ID,
                name="Test Region",
                county="Test",
                state_id=options["state"],
                hidden=True,
            )
            region.save()

            # Create an office
            office = Office(
                external_id=TEST_OFFICE_ID, hours="", notes="", region=region,
            )

            office.save()

            # Create a an address

            address = Address(
                external_id=TEST_ADDRESS_ID,
                office=office,
                address="Test Office",
                address2="123 Test Street",
                address3="Ste 123",
                city="Test",
                state_id=options["state"],
                zipcode="12345",
                website="",
                email=options["email"],
                phone="",
                fax=options["fax"],
                is_physical=True,
                is_regular_mail=True,
                process_domestic_registrations=True,
                process_absentee_requests=True,
                process_absentee_ballots=True,
                process_overseas_requests=True,
                process_overseas_ballots=True,
            )

            address.save()
