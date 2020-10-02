from django.db import migrations, models

import common.enums
import common.fields

from . import DASHBOARD_VIEWS_CREATE_SQL, DASHBOARD_VIEWS_DROP_SQL

class Migration(migrations.Migration):

    dependencies = [
        ("absentee", "0023_print_and_forward"),
    ]

    operations = [
        migrations.RunSQL(
            DASHBOARD_VIEWS_CREATE_SQL, reverse_sql=DASHBOARD_VIEWS_DROP_SQL
        ),
    ]
