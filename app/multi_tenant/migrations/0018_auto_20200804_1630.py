# Generated by Django 2.2.15 on 2020-08-04 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multi_tenant', '0017_smalluuid_to_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='has_api_access',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
