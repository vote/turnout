# Generated by Django 2.2.16 on 2020-11-06 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verifier', '0023_index_phone'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='lookup',
            index=models.Index(fields=['created_at'], name='verifier_lo_created_1c955c_idx'),
        ),
    ]