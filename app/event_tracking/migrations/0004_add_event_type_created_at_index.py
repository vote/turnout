# Generated by Django 2.2.14 on 2020-07-21 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event_tracking', '0003_event_type_db_index'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['event_type', 'created_at'], name='event_track_event_t_63c029_idx'),
        ),
    ]
