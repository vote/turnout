# Generated by Django 2.2.16 on 2020-10-20 19:42

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('smsbot', '0007_smsmessage_twilio_sid'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsmessage',
            name='kwargs',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
    ]