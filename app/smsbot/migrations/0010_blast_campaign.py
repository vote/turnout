# Generated by Django 2.2.16 on 2020-10-27 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smsbot', '0009_blast'),
    ]

    operations = [
        migrations.AddField(
            model_name='blast',
            name='campaign',
            field=models.TextField(null=True),
        ),
    ]
