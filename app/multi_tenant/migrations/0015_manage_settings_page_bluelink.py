# Generated by Django 2.2.14 on 2020-07-13 01:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multi_tenant', '0014_subscriberintegrationproperty'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='sync_bluelink',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AlterField(
            model_name='client',
            name='privacy_policy',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='client',
            name='sms_enabled',
            field=models.BooleanField(default=True, null=True),
        ),
        migrations.AlterField(
            model_name='client',
            name='terms_of_service',
            field=models.URLField(blank=True, null=True),
        ),
    ]
