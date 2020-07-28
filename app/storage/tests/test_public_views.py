from datetime import datetime

import pytest
import pytz
from model_bakery import baker
from smalluuid import SmallUUID

from common import enums
from event_tracking.models import Event
from storage.models import StorageItem


@pytest.mark.django_db
def test_registration_download_tracks_event(client):
    storage_item = baker.make_recipe("storage.registration_form")
    registration = baker.make_recipe("register.registration", result_item=storage_item)

    client.get(f"/download/{storage_item.pk}/?token={storage_item.token}", follow=False)

    assert Event.objects.count() == 1
    first_event = Event.objects.first()
    assert first_event.action == registration.action
    assert first_event.event_type == enums.EventType.DOWNLOAD


@pytest.mark.django_db
def test_ballot_request_download_tracks_event(client):
    storage_item = baker.make_recipe("storage.ballot_request_form")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", result_item=storage_item
    )

    client.get(f"/download/{storage_item.pk}/?token={storage_item.token}", follow=False)

    assert Event.objects.count() == 1
    first_event = Event.objects.first()
    assert first_event.action == ballot_request.action
    assert first_event.event_type == enums.EventType.DOWNLOAD


@pytest.mark.django_db
def test_track_first_download(client, freezer):
    freezer.move_to("2009-01-20 11:30:00")
    storage_item = baker.make_recipe("storage.registration_form")
    registration = baker.make_recipe("register.registration", result_item=storage_item)

    client.get(f"/download/{storage_item.pk}/?token={storage_item.token}", follow=False)

    refreshed_item = StorageItem.objects.get(pk=storage_item.pk)
    assert refreshed_item.first_download == datetime(
        2009, 1, 20, 11, 30, tzinfo=pytz.utc
    )


@pytest.mark.django_db
def test_smalluuid_key(client):
    storage_item = baker.make_recipe("storage.registration_form")
    registration = baker.make_recipe("register.registration", result_item=storage_item)

    smalluuid = SmallUUID(bytes=storage_item.pk.bytes)

    client.get(f"/download/{smalluuid}/?token={storage_item.token}", follow=False)

    assert Event.objects.count() == 1
    first_event = Event.objects.first()
    assert first_event.action == registration.action
