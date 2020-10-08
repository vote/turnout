import django.db.models.deletion
from django.db import migrations, models

from reporting.migrations import VIEW_CREATE_SQL, VIEW_DROP_SQL


class Migration(migrations.Migration):

    dependencies = [
        ("reporting", "0007_refresh_views"),
    ]

    operations = [
        migrations.RunSQL(VIEW_CREATE_SQL),
    ]
