import datetime
from uuid import uuid4

import pytest
from django.conf import settings
from model_bakery import baker
from smalluuid import SmallUUID

import storage.tasks

STORAGE_RESET_URL = "/v1/storage/reset/"
STORAGE_DOWNLOAD_URL = "/download/"


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


@pytest.mark.django_db
def test_purge(client):
    created = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
        days=10
    )

    reg_item = baker.make_recipe("storage.registration_form")
    reg_item.created_at = created
    reg_item.save()

    settings.FILE_PURGE_DAYS = None
    storage.tasks.purge_old_storage()
    reg_item.refresh_from_db()
    assert not reg_item.purged

    settings.FILE_PURGE_DAYS = 15
    storage.tasks.purge_old_storage()
    reg_item.refresh_from_db()
    assert not reg_item.purged

    settings.FILE_PURGE_DAYS = 5
    storage.tasks.purge_old_storage()
    reg_item.refresh_from_db()
    assert reg_item.purged


@pytest.mark.django_db
def test_purge_ballot_request_form(client):
    settings.FILE_PURGE_DAYS = 24

    ballot_item = baker.make_recipe("storage.ballot_request_form")
    ballot_item.created_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    ballot_item.save()

    storage.tasks.purge_old_storage()

    ballot_item.refresh_from_db()
    assert ballot_item.purged
    assert not ballot_item.file.name


@pytest.mark.django_db
def test_purge_registration_form(client):
    settings.FILE_PURGE_DAYS = 24

    reg_item = baker.make_recipe("storage.registration_form")
    reg_item.created_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    reg_item.save()

    storage.tasks.purge_old_storage()

    reg_item.refresh_from_db()
    assert reg_item.purged
    assert not reg_item.file.name

    resp = client.post(STORAGE_RESET_URL, {"id": str(reg_item.uuid)})
    assert resp.status_code == 302

    resp = client.get(f"{STORAGE_DOWNLOAD_URL}{str(reg_item.uuid)}/")
    assert resp.status_code == 302


@pytest.mark.django_db
def test_purge_secureupload(client):
    upload = baker.make_recipe("storage.secureupload")
    upload.created_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    upload.save()

    storage.tasks.purge_old_storage()

    upload.refresh_from_db()
    assert upload.purged
    assert not upload.file.name
