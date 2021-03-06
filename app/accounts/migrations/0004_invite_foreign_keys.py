# Generated by Django 2.2.9 on 2020-02-10 20:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('multi_tenant', '0004_inviteassociation'),
        ('accounts', '0003_invite'),
    ]

    operations = [
        migrations.AddField(
            model_name='invite',
            name='clients',
            field=models.ManyToManyField(through='multi_tenant.InviteAssociation', to='multi_tenant.Client'),
        ),
        migrations.AddField(
            model_name='invite',
            name='primary_client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='invited_client', to='multi_tenant.Client'),
        ),
        migrations.AddField(
            model_name='invite',
            name='user',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
