import django.db.models.deletion
from django.db import migrations, models

from action.migrations import (
    ACTIONDETAIL_VIEW_CREATION_SQL,
    ACTIONDETAIL_VIEW_REVERSE_SQL,
)


class Migration(migrations.Migration):

    dependencies = [
        ("action", "0006_smalluuid_to_uuid"),
    ]

    operations = [
        migrations.RunSQL(ACTIONDETAIL_VIEW_CREATION_SQL),
    ]
