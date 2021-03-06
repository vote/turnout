# Generated by Django 2.2.12 on 2020-05-28 20:01

import django.db.models.deletion
import django_smalluuid.models
from django.db import migrations, models

import common.enums
import common.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("storage", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Fax",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "uuid",
                    django_smalluuid.models.SmallUUIDField(
                        default=django_smalluuid.models.UUIDDefault(),
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "token",
                    django_smalluuid.models.SmallUUIDField(
                        default=django_smalluuid.models.UUIDDefault(), unique=True
                    ),
                ),
                ("status", common.fields.TurnoutEnumField(enum=common.enums.FaxStatus)),
                ("status_message", models.TextField(null=True)),
                ("status_timestamp", models.DateTimeField(null=True)),
                (
                    "storage_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="storage.StorageItem",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"],},
        ),
    ]
