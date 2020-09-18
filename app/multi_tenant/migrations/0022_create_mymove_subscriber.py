
from django.db import migrations
from common.enums import SubscriberStatus

def create_mymove_subscriber(apps, schema_editor):
    Client = apps.get_model('multi_tenant', 'Client')
    SubscriberSlug = apps.get_model('multi_tenant', 'SubscriberSlug')
    existing = Client.objects.filter(name='MyMove').first()
    if not existing:
        subscriber = Client.objects.create(
            name="MyMove",
            url="https://mymove.com/",
            status=SubscriberStatus.ACTIVE,
            sms_enabled=False,
        )
        slug = SubscriberSlug.objects.create(
            slug="mymove",
            subscriber=subscriber,
        )
        subscriber.default_slug = slug
        subscriber.save()


class Migration(migrations.Migration):

    dependencies = [
        ('multi_tenant', '0021_change_default_email'),
    ]

    operations = [
        migrations.RunPython(create_mymove_subscriber, lambda x,y: None)
    ]
