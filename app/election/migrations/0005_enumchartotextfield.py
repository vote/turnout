# Generated by Django 2.2.12 on 2020-04-17 02:36

import common.enums
import common.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('election', '0004_updatenotificationwebhook'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stateinformationfieldtype',
            name='field_format',
            field=common.fields.TurnoutEnumField(default='Markdown', enum=common.enums.StateFieldFormats, null=True),
        ),
        migrations.AlterField(
            model_name='updatenotificationwebhook',
            name='type',
            field=common.fields.TurnoutEnumField(enum=common.enums.NotificationWebhookTypes, null=True),
        ),
    ]
