# Generated by Django 2.2.14 on 2020-07-06 19:46

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0016_tracking_embed_url_session_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='state_api_result',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='registration',
            name='state_fields',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
