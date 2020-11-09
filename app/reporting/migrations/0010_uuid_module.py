import django.db.models.deletion
from django.db import migrations, models

from reporting.migrations import VIEW_CREATE_SQL, VIEW_DROP_SQL


class Migration(migrations.Migration):

    dependencies = [
        ("reporting", "0009_statsrefresh_subscriberstats"),
    ]

    operations = [
        migrations.RunSQL('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'),
    ]
