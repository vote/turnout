# Generated by Django 2.2.12 on 2020-05-18 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verifier', '0014_lookup_sms_opt_in_partner'),
    ]

    operations = [
        migrations.AddField(
            model_name='lookup',
            name='utm_content',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lookup',
            name='utm_term',
            field=models.TextField(blank=True, null=True),
        ),
    ]
