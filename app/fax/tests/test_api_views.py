import uuid
from datetime import datetime, timedelta, timezone

import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from common.enums import FaxStatus
from fax.api_views import handle_fax_callback
from fax.models import Fax

FAX_STATUS_CALLBACK_ENDPOINT = "/v1/fax/gateway_callback/"


@pytest.mark.django_db
def test_handle_fax_callback(mocker):
    ts = datetime(2020, 6, 1, 1, 2, 3, tzinfo=timezone.utc)

    mock_celery = mocker.patch("fax.api_views.app")

    fax = baker.make_recipe(
        "fax.fax", on_complete_task="some_task", on_complete_task_arg="asdf"
    )

    handle_fax_callback(
        {"status": FaxStatus.SENT, "message": "some message", "timestamp": ts}, fax,
    )

    new_fax = Fax.objects.get(pk=fax.uuid)

    assert fax.status == FaxStatus.SENT
    assert fax.status_message == "some message"
    assert fax.status_timestamp == ts

    mock_celery.send_task.assert_called_with(
        "some_task", args=[str(FaxStatus.SENT), "asdf"]
    )


@pytest.mark.django_db
def test_handle_fax_callback_tmp_fail(mocker):
    ts = datetime(2020, 6, 1, 1, 2, 3, tzinfo=timezone.utc)

    mock_celery = mocker.patch("fax.api_views.app")

    fax = baker.make_recipe(
        "fax.fax", on_complete_task="some_task", on_complete_task_arg="asdf"
    )

    handle_fax_callback(
        {
            "status": FaxStatus.TEMPORARY_FAILURE,
            "message": "some message",
            "timestamp": ts,
        },
        fax,
    )

    new_fax = Fax.objects.get(pk=fax.uuid)

    assert fax.status == FaxStatus.TEMPORARY_FAILURE
    assert fax.status_message == "some message"
    assert fax.status_timestamp == ts

    assert not mock_celery.send_task.called


@pytest.mark.django_db
def test_handle_fax_callback_perm_fail(mocker):
    ts = datetime(2020, 6, 1, 1, 2, 3, tzinfo=timezone.utc)

    mock_celery = mocker.patch("fax.api_views.app")

    fax = baker.make_recipe(
        "fax.fax", on_complete_task="some_task", on_complete_task_arg="asdf"
    )

    handle_fax_callback(
        {
            "status": FaxStatus.PERMANENT_FAILURE,
            "message": "some message",
            "timestamp": ts,
        },
        fax,
    )

    new_fax = Fax.objects.get(pk=fax.uuid)

    assert fax.status == FaxStatus.PERMANENT_FAILURE
    assert fax.status_message == "some message"
    assert fax.status_timestamp == ts

    mock_celery.send_task.assert_called_with(
        "some_task", args=[str(FaxStatus.PERMANENT_FAILURE), "asdf"]
    )


@pytest.mark.django_db
def test_callback(mocker):
    ts = datetime(2020, 6, 1, 1, 2, 3, tzinfo=timezone.utc)
    token = uuid.uuid4()

    mock_handle = mocker.patch("fax.api_views.handle_fax_callback")
    mock_statsd = mocker.patch("fax.api_views.statsd")
    client = APIClient()

    fax = baker.make_recipe("fax.fax", token=token)

    response = client.post(
        f"{FAX_STATUS_CALLBACK_ENDPOINT}?token={str(token)}",
        {
            "fax_id": str(fax.uuid),
            "status": "sent",
            "message": "some message",
            "timestamp": int(ts.timestamp()),
        },
        format="json",
    )

    assert response.status_code == 200

    mock_handle.assert_called_with(
        {
            "fax_id": fax.uuid,
            "message": "some message",
            "timestamp": ts,
            "status": FaxStatus.SENT,
        },
        fax,
    )
    assert not mock_statsd.increment.called


@pytest.mark.django_db
def test_callback_no_fax(mocker):
    ts = datetime(2020, 6, 1, 1, 2, 3, tzinfo=timezone.utc)
    token = uuid.uuid4()
    wrong_id = uuid.uuid4()

    mock_handle = mocker.patch("fax.api_views.handle_fax_callback")
    mock_statsd = mocker.patch("fax.api_views.statsd")
    client = APIClient()

    fax = baker.make_recipe("fax.fax", token=token)

    response = client.post(
        f"{FAX_STATUS_CALLBACK_ENDPOINT}?token={str(token)}",
        {
            "fax_id": str(wrong_id),
            "status": "sent",
            "message": "some message",
            "timestamp": int(ts.timestamp()),
        },
        format="json",
    )

    assert response.status_code == 404
    mock_statsd.increment.assert_called_with("turnout.fax.callback.fax_does_not_exist")

    assert not mock_handle.called


@pytest.mark.django_db
def test_callback_wrong_token(mocker):
    ts = datetime(2020, 6, 1, 1, 2, 3, tzinfo=timezone.utc)
    token = uuid.uuid4()
    wrong_token = uuid.uuid4()

    mock_handle = mocker.patch("fax.api_views.handle_fax_callback")
    mock_statsd = mocker.patch("fax.api_views.statsd")
    client = APIClient()

    fax = baker.make_recipe("fax.fax", token=token)

    response = client.post(
        f"{FAX_STATUS_CALLBACK_ENDPOINT}?token={str(wrong_token)}",
        {
            "fax_id": str(fax.uuid),
            "status": "sent",
            "message": "some message",
            "timestamp": int(ts.timestamp()),
        },
        format="json",
    )

    assert response.status_code == 403
    mock_statsd.increment.assert_called_with("turnout.fax.callback.wrong_token")

    assert not mock_handle.called


@pytest.mark.django_db
def test_callback_no_token(mocker):
    ts = datetime(2020, 6, 1, 1, 2, 3, tzinfo=timezone.utc)
    token = uuid.uuid4()

    mock_handle = mocker.patch("fax.api_views.handle_fax_callback")
    mock_statsd = mocker.patch("fax.api_views.statsd")
    client = APIClient()

    fax = baker.make_recipe("fax.fax", token=token)

    response = client.post(
        f"{FAX_STATUS_CALLBACK_ENDPOINT}",
        {
            "fax_id": str(fax.uuid),
            "status": "sent",
            "message": "some message",
            "timestamp": int(ts.timestamp()),
        },
        format="json",
    )

    assert response.status_code == 400
    mock_statsd.increment.assert_called_with("turnout.fax.callback.no_token")

    assert not mock_handle.called


@pytest.mark.django_db
def test_callback_old_timestamp(mocker):
    ts = datetime(2020, 6, 1, 1, 2, 3, tzinfo=timezone.utc)
    token = uuid.uuid4()

    mock_handle = mocker.patch("fax.api_views.handle_fax_callback")
    mock_statsd = mocker.patch("fax.api_views.statsd")
    client = APIClient()

    fax = baker.make_recipe("fax.fax", token=token, status_timestamp=ts)

    response = client.post(
        f"{FAX_STATUS_CALLBACK_ENDPOINT}?token={str(token)}",
        {
            "fax_id": str(fax.uuid),
            "status": "sent",
            "message": "some message",
            "timestamp": int(ts.timestamp()) - 1,
        },
        format="json",
    )

    assert response.status_code == 200
    mock_statsd.increment.assert_called_with("turnout.fax.callback.outdated_timestamp")

    assert not mock_handle.called


@pytest.mark.django_db
def test_callback_new_timestamp(mocker):
    ts = datetime(2020, 6, 1, 1, 2, 3, tzinfo=timezone.utc)
    token = uuid.uuid4()

    mock_handle = mocker.patch("fax.api_views.handle_fax_callback")
    mock_statsd = mocker.patch("fax.api_views.statsd")
    client = APIClient()

    fax = baker.make_recipe("fax.fax", token=token, status_timestamp=ts)

    response = client.post(
        f"{FAX_STATUS_CALLBACK_ENDPOINT}?token={str(token)}",
        {
            "fax_id": str(fax.uuid),
            "status": "sent",
            "message": "some message",
            "timestamp": int(ts.timestamp()) + 1,
        },
        format="json",
    )

    assert response.status_code == 200
    assert not mock_statsd.increment.called

    mock_handle.assert_called_with(
        {
            "fax_id": fax.uuid,
            "message": "some message",
            "timestamp": ts + timedelta(seconds=1),
            "status": FaxStatus.SENT,
        },
        fax,
    )


@pytest.mark.django_db
def test_callback_bad_request(mocker):
    ts = datetime(2020, 6, 1, 1, 2, 3, tzinfo=timezone.utc)
    token = uuid.uuid4()

    mock_handle = mocker.patch("fax.api_views.handle_fax_callback")
    mocker.patch("fax.api_views.statsd")
    client = APIClient()

    fax = baker.make_recipe("fax.fax", token=token)

    response = client.post(
        f"{FAX_STATUS_CALLBACK_ENDPOINT}?token={str(token)}",
        {
            "fax_id": str(fax.uuid),
            "status": "xxx",
            "message": "some message",
            "timestamp": int(ts.timestamp()),
        },
        format="json",
    )

    assert response.status_code == 400

    assert not mock_handle.called
