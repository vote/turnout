from django.db import migrations, models
from common import enums


def change_sms_options(apps, schema_editor):
    Client = apps.get_model("multi_tenant", "Client")
    for client in Client.objects.all():
        if client.sms_enabled and not client.sms_checkbox:
            client.sms_checkbox = True
            client.sms_checkbox_default = True
            client.save()


class Migration(migrations.Migration):

    dependencies = [
        ("multi_tenant", "0024_migrate_to_public_subscriber"),
    ]

    operations = [migrations.RunPython(change_sms_options, lambda x, y: None)]
