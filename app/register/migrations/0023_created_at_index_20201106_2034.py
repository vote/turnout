# Generated by Django 2.2.16 on 2020-11-06 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0022_index_phone'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='registration',
            index=models.Index(fields=['created_at'], name='register_re_created_818a3a_idx'),
        ),
    ]
