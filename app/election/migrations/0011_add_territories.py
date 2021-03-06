# Generated by Django 2.2.9 on 2019-12-20 01:14

from django.db import migrations

from election.choices import TERRITORIES


def create_states(apps, schema_editor):
    State = apps.get_model("election", "State")
    for state in TERRITORIES:
        State.objects.get_or_create(code=state[0], name=state[1])


class Migration(migrations.Migration):

    dependencies = [
        ("election", "0010_smalluuid_to_uuid"),
    ]

    operations = [migrations.RunPython(create_states, lambda x, y: None)]
