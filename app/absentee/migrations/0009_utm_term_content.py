# Generated by Django 2.2.12 on 2020-05-18 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('absentee', '0008_absenteeleoemailoverride'),
    ]

    operations = [
        migrations.AddField(
            model_name='ballotrequest',
            name='utm_content',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ballotrequest',
            name='utm_term',
            field=models.TextField(blank=True, null=True),
        ),
    ]
