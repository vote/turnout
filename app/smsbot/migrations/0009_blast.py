# Generated by Django 2.2.16 on 2020-10-20 22:16

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('smsbot', '0008_smsmessage_kwargs'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blast',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('description', models.TextField(null=True)),
                ('content', models.TextField(null=True)),
                ('sql', models.TextField(null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='smsmessage',
            name='blast',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='smsbot.Blast'),
        ),
    ]