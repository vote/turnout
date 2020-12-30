from django.db import migrations
from django.db.models import Q
from django.conf import settings
from common.enums import SubscriberStatus


def migrate_to_public_subscriber(apps, schema_editor):
    Client = apps.get_model("multi_tenant", "Client")

    Registration = apps.get_model("register", "Registration")
    BallotRequest = apps.get_model("absentee", "BallotRequest")
    PollingPlaceLookup = apps.get_model("polling_place", "PollingPlaceLookup")
    ReminderRequest = apps.get_model("reminder", "ReminderRequest")
    Lookup = apps.get_model("verifier", "Lookup")

    public_subscriber = Client.objects.get(default_slug__slug="public")
    default_subscriber = Client.objects.first()

    for Model in (
        Registration,
        BallotRequest,
        PollingPlaceLookup,
        ReminderRequest,
        Lookup,
    ):
        Model.objects.filter(
            Q(subscriber=default_subscriber)
            & ~Q(embed_url__icontains=settings.WWW_ORIGIN)
            & Q(embed_url__isnull=False)
        ).update(subscriber=public_subscriber)


def migrate_from_public_subscriber(apps, schema_editor):
    Client = apps.get_model("multi_tenant", "Client")

    Registration = apps.get_model("register", "Registration")
    BallotRequest = apps.get_model("absentee", "BallotRequest")
    PollingPlaceLookup = apps.get_model("polling_place", "PollingPlaceLookup")
    ReminderRequest = apps.get_model("reminder", "ReminderRequest")
    Lookup = apps.get_model("verifier", "Lookup")

    public_subscriber = Client.objects.get(default_slug__slug="public")
    default_subscriber = Client.objects.first()

    for Model in (
        Registration,
        BallotRequest,
        PollingPlaceLookup,
        ReminderRequest,
        Lookup,
    ):
        Model.objects.filter(subscriber=public_subscriber).update(
            subscriber=default_subscriber
        )


class Migration(migrations.Migration):

    dependencies = [
        ("multi_tenant", "0023_create_public_subscriber"),
        ("register", "0023_created_at_index_20201106_2034"),
        ("absentee", "0026_created_at_index_20201106_2034"),
        ("polling_place", "0002_created_at_index_20201106_2034"),
        ("reminder", "0004_index_phone"),
        ("verifier", "0024_created_at_index_20201106_2034"),
    ]

    operations = [
        migrations.RunPython(
            migrate_to_public_subscriber, migrate_from_public_subscriber
        )
    ]
