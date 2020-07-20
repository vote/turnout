# Generated by Django 2.2.14 on 2020-07-20 14:21

import common.enums
import common.fields
from django.db import migrations, models
import django.db.models.deletion
import django_smalluuid.models


class Migration(migrations.Migration):

    dependencies = [
        ('multi_tenant', '0015_manage_settings_page_bluelink'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='active',
            field=models.BooleanField(null=True),
        ),
        migrations.CreateModel(
            name='SubscriptionInterval',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('uuid', django_smalluuid.models.SmallUUIDField(default=django_smalluuid.models.UUIDDefault(), editable=False, primary_key=True, serialize=False, unique=True)),
                ('begin', models.DateTimeField(null=True)),
                ('end', models.DateTimeField(null=True)),
                ('subscriber', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='multi_tenant.Client')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubscriberLead',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('uuid', django_smalluuid.models.SmallUUIDField(default=django_smalluuid.models.UUIDDefault(), editable=False, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('url', models.URLField()),
                ('email', models.EmailField(max_length=254, null=True)),
                ('slug', models.CharField(max_length=40, null=True)),
                ('is_c3', models.BooleanField(null=True)),
                ('status', common.fields.TurnoutEnumField(enum=common.enums.SubscriberLeadStatus, null=True)),
                ('stripe_customer_id', models.TextField(null=True)),
                ('subscriber', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='multi_tenant.Client')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='client',
            name='active_subscription',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='multi_tenant.SubscriptionInterval'),
        ),
    ]
