from django.core.management.base import BaseCommand

from apikey.models import ApiKey
from multi_tenant.models import Client


class Command(BaseCommand):
    help = "Create an API key"
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument("subscriber", type=str)

    def handle(self, *args, **options):
        client = Client.objects.get(default_slug__slug=options["subscriber"])
        key = ApiKey(subscriber=client)

        key.save()

        print(f"Key ID: {key.uuid}")
        print(f"Key Secret: {key.hashed_secret()}")
