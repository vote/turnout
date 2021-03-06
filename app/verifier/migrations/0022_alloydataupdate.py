# Generated by Django 2.2.16 on 2020-09-19 19:41

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('verifier', '0021_multi_vendor'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlloyDataUpdate',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('state', models.TextField(null=True)),
                ('state_update_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
