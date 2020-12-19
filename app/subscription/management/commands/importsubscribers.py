from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Import Bulk Subscriber Updates"
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        from subscription.models import Subscription
        from common import enums
        import csv

        file = options["file"]

        with open(file, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:

                print(row["Subscriber Slug"], row["Primary Contact First Name"])
                subscription = Subscription.objects.filter(
                    subscriber__default_slug__slug=row["Subscriber Slug"]
                ).first()

                if row["Primary Contact First Name"]:
                    subscription.primary_contact_first_name = row[
                        "Primary Contact First Name"
                    ]

                if row["Primary Contact Last Name"]:
                    subscription.primary_contact_last_name = row[
                        "Primary Contact Last Name"
                    ]

                if row["Primary Contact Email"]:
                    subscription.primary_contact_email = row["Primary Contact Email"]

                if row["Primary Contact Phone"]:
                    subscription.primary_contact_phone = row["Primary Contact Phone"]

                if row["EIN"]:
                    subscription.ein = row["EIN"]

                if row["Plan"]:
                    subscription.plan = enums.SubscriberPlan[row["Plan"].upper()]

                if row["Internal Notes"]:
                    subscription.internal_notes = row["Internal Notes"]

                subscription.save()
