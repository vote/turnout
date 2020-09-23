
from django.db import migrations
from django.conf import settings
from common.enums import SubscriberStatus

def create_mover_subscriber(apps, schema_editor):
    Client = apps.get_model('multi_tenant', 'Client')
    SubscriberSlug = apps.get_model('multi_tenant', 'SubscriberSlug')
    source = settings.MOVER_SOURCE or "moverleadsource"
    existing = Client.objects.filter(name=source).first()
    if not existing:
        subscriber = Client.objects.create(
            name=source,
            url=f"https://{source}.com/",
            status=SubscriberStatus.ACTIVE,
            sms_enabled=False,
        )
        slug = SubscriberSlug.objects.create(
            slug=source,
            subscriber=subscriber,
        )
        subscriber.default_slug = slug
        subscriber.save()


class Migration(migrations.Migration):

    dependencies = [
        ('multi_tenant', '0021_change_default_email'),
    ]

    operations = [
        migrations.RunPython(create_mover_subscriber, lambda x,y: None)
    ]
