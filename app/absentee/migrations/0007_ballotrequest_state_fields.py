# Generated by Django 2.2.12 on 2020-05-07 21:52

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('absentee', '0006_ballotrequest_signature'),
    ]

    operations = [
        migrations.AddField(
            model_name='ballotrequest',
            name='state_fields',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
    ]
