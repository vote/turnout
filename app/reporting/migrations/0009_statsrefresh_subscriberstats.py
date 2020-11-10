# Generated by Django 2.2.16 on 2020-11-06 19:18

import common.enums
import common.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid
from datetime import datetime, timezone


def create_stats_refresh(apps, schema_editor):
    StatsRefresh = apps.get_model("reporting", "StatsRefresh")
    StatsRefresh(last_run=datetime(1900, 1, 1, 0, 0, 0, tzinfo=timezone.utc)).save()


class Migration(migrations.Migration):

    dependencies = [
        ("multi_tenant", "0022_create_mover_subscriber"),
        ("reporting", "0008_refresh_views"),
    ]

    operations = [
        migrations.CreateModel(
            name="StatsRefresh",
            fields=[
                ("last_run", models.DateTimeField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name="SubscriberStats",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("tool", common.fields.TurnoutEnumField(enum=common.enums.ToolName)),
                ("count", models.BigIntegerField()),
                (
                    "subscriber",
                    models.ForeignKey(
                        db_column="partner_id",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="multi_tenant.Client",
                    ),
                ),
            ],
            options={"unique_together": {("subscriber", "tool")},},
        ),
        migrations.RunPython(create_stats_refresh, lambda x, y: None),
    ]