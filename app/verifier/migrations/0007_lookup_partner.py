# Generated by Django 2.2.11 on 2020-03-31 16:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('multi_tenant', '0004_inviteassociation'),
        ('verifier', '0006_add_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='lookup',
            name='partner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='multi_tenant.Client'),
        ),
    ]
