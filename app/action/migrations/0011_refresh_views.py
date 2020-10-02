import django.db.models.deletion
from django.db import migrations, models

from action.migrations import (
    ACTIONDETAIL_VIEW_CREATION_SQL,
    ACTIONDETAIL_VIEW_REVERSE_SQL,
)


class Migration(migrations.Migration):

    dependencies = [
        ("action", "0010_index_last_voter_lookup"),
    ]

    operations = [
        migrations.RunSQL(ACTIONDETAIL_VIEW_CREATION_SQL),
    ]
