import pytest
from model_bakery import baker
from smalluuid import SmallUUID
from uuid import uuid4

from common import enums
from event_tracking.models import Event
from storage.models import StorageItem

STORAGE_RESET_URL = "/v1/storage/reset/"


@pytest.mark.django_db
def test_reset_uuid(client):
    storage_item = baker.make_recipe("storage.registration_form")
    old_token = storage_item.token
    old_expires = storage_item.expires

    resp = client.post(STORAGE_RESET_URL, {"id": str(storage_item.uuid)})

    assert resp.status_code == 201
    storage_item.refresh_from_db()

    assert storage_item.token != old_token
    assert storage_item.expires > old_expires


@pytest.mark.django_db
def test_reset_smalluuid(client):
    storage_item = baker.make_recipe("storage.registration_form")
    old_token = storage_item.token
    old_expires = storage_item.expires

    smalluuid = SmallUUID(hex=str(storage_item.uuid))

    resp = client.post(STORAGE_RESET_URL, {"id": str(smalluuid)})

    assert resp.status_code == 201
    storage_item.refresh_from_db()

    assert storage_item.token != old_token
    assert storage_item.expires > old_expires


def test_reset_no_id(client):
    resp = client.post(STORAGE_RESET_URL, {})

    assert resp.status_code == 400
    assert resp.json() == {"id": "Required"}


def test_reset_invalid_id(client):
    resp = client.post(STORAGE_RESET_URL, {"id": "xxx"})

    assert resp.status_code == 400
    assert resp.json() == {"id": "Must be a uuid or smalluuid"}

    resp = client.post(STORAGE_RESET_URL, {"id": 123})

    assert resp.status_code == 400
    assert resp.json() == {"id": "Must be a uuid or smalluuid"}


@pytest.mark.django_db
def test_reset_no_such_id(client):
    resp = client.post(STORAGE_RESET_URL, {"id": uuid4()})

    assert resp.status_code == 404
