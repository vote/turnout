# Generated by Django 2.2.13 on 2020-06-24 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('election', '0006_state_vbm_submission_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='stateinformationfieldtype',
            name='help_text',
            field=models.TextField(blank=True, help_text='Markdown allowed', null=True, verbose_name='Help Text'),
        ),
    ]
