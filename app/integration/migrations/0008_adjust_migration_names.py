
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('integration', '0007_rename_moverlead_table'),
    ]

    operations = [
        migrations.RunSQL(
            "UPDATE django_migrations SET name='0003_moverlead' WHERE app='integration' AND name LIKE '0003%'"
        ),
        migrations.RunSQL(
            "UPDATE django_migrations SET name='0004_mover_state_drop_foreign_key' WHERE app='integration' AND name LIKE '0004%'"
        ),
        migrations.RunSQL(
            "UPDATE django_migrations SET name='0005_mover_regions' WHERE app='integration' AND name LIKE '0005%'"
        ),
        migrations.RunSQL(
            "UPDATE django_migrations SET name='0006_mover_blank_forms_fields' WHERE app='integration' AND name LIKE '0006%'"
        ),
        migrations.RunSQL(
            "UPDATE django_migrations SET name='0022_create_mover_subscriber' WHERE app='multi_tenant' AND name LIKE '0022%'"
        ),
    ]
