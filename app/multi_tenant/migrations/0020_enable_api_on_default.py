
from django.db import migrations

def enable_api_on_default(apps, schema_editor):
    Client = apps.get_model('multi_tenant', 'Client')
    for client in Client.objects.filter(name='Default'):
        client.has_api_access = True
        client.save()


class Migration(migrations.Migration):

    dependencies = [
        ('multi_tenant', '0019_auto_20200804_2120'),
    ]

    operations = [
        migrations.RunPython(enable_api_on_default, lambda x,y: None)
    ]
