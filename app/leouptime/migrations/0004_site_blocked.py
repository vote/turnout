# Generated by Django 2.2.16 on 2020-09-08 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leouptime', '0003_sitecheck_blocked'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='blocked',
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='blocked_changed_at',
            field=models.DateTimeField(null=True),
        ),
    ]
