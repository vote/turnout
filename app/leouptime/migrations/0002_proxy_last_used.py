# Generated by Django 2.2.16 on 2020-09-06 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leouptime', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='proxy',
            name='last_used',
            field=models.DateTimeField(null=True),
        ),
    ]