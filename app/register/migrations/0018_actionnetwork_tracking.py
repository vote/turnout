# Generated by Django 2.2.14 on 2020-07-16 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0017_auto_20200706_1946'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='email_referrer',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='registration',
            name='mobile_referrer',
            field=models.TextField(blank=True, null=True),
        ),
    ]
