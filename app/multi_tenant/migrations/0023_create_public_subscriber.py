from django.db import migrations
from django.conf import settings
from common.enums import SubscriberStatus


def create_public_subscriber(apps, schema_editor):
    Client = apps.get_model("multi_tenant", "Client")
    SubscriberSlug = apps.get_model("multi_tenant", "SubscriberSlug")

    existing_slug = SubscriberSlug.objects.filter(slug="public").first()
    if existing_slug:
        existing_slug.delete()

    subscriber = Client.objects.create(
        name="Public Tool Embeds",
        url=f"https://docs.voteamerica.com/embed/free/",
        status=SubscriberStatus.ACTIVE,
        is_first_party=True,
        # This "subscriber" doesn't have a subscriber-specific SMS opt-in,
        # just the default VoteAmerica SMS opt-in.
        sms_enabled=False,
    )
    slug = SubscriberSlug.objects.create(
        slug="public",
        subscriber=subscriber,
    )
    subscriber.default_slug = slug
    subscriber.save()


def delete_public_subscriber(apps, schema_editor):
    Client = apps.get_model("multi_tenant", "Client")
    SubscriberSlug = apps.get_model("multi_tenant", "SubscriberSlug")

    existing_client = Client.objects.filter(default_slug__slug="public").first()
    if existing_client:
        existing_client.default_slug = None
        existing_client.save()
        existing_client.delete()

    existing_slug = SubscriberSlug.objects.filter(slug="public").first()
    if existing_slug:
        existing_slug.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("multi_tenant", "0022_create_mover_subscriber"),
    ]

    operations = [
        migrations.RunPython(create_public_subscriber, delete_public_subscriber)
    ]
