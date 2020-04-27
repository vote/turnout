# Generated by Django 2.2.12 on 2020-04-17 02:36

import common.enums
import common.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('verifier', '0011_sms_opt_in_nullable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lookup',
            name='gender',
            field=common.fields.TurnoutEnumField(enum=common.enums.TargetSmartGender, null=True),
        ),
        migrations.AlterField(
            model_name='lookup',
            name='voter_status',
            field=common.fields.TurnoutEnumField(enum=common.enums.VoterStatus, null=True),
        ),
    ]