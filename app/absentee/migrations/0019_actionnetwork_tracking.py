# Generated by Django 2.2.14 on 2020-07-16 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('absentee', '0018_leocontactoverride_submission_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='ballotrequest',
            name='email_referrer',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ballotrequest',
            name='mobile_referrer',
            field=models.TextField(blank=True, null=True),
        ),
    ]
