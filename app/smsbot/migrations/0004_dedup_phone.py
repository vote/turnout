from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("smsbot", "0003_auto_20200804_1546"),
    ]

    operations = [
        migrations.RunSQL(
            """
DELETE FROM smsbot_number
WHERE ctid NOT IN (
    SELECT min(ctid)
    FROM smsbot_number
    GROUP BY phone);
            """
        )
    ]
