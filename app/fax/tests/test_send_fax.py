# Disable, no override
# Disabled, with override
# Live

import json
from datetime import datetime, timezone

import pytest
from model_bakery import baker

from common.enums import FaxStatus
from fax.models import Fax
from fax.send_fax import send_fax


@pytest.fixture
def mock_sqs_client(mocker):
    return mocker.patch("fax.send_fax.sqs_client")


@pytest.fixture
def mock_handle_callback(mocker):
    return mocker.patch("fax.send_fax.handle_fax_callback")


@pytest.mark.django_db
def test_send_fax(settings, mock_sqs_client):
    settings.FAX_DISABLE = False
    settings.FAX_OVERRIDE_DEST = None
    settings.FAX_GATEWAY_SQS_QUEUE = "some-queue"
    settings.FAX_GATEWAY_CALLBACK_URL = "some-url"

    storage_item = baker.make_recipe("storage.ballot_request_form")

    send_fax(storage_item, "+16175551234", "some_task", "some_task_arg")

    fax = Fax.objects.get(storage_item=storage_item)

    assert fax.to == "+16175551234"
    assert fax.status == FaxStatus.PENDING
    assert fax.on_complete_task == "some_task"
    assert fax.on_complete_task_arg == "some_task_arg"

    mock_sqs_client.send_message.assert_called_with(
        QueueUrl="some-queue",
        MessageBody=json.dumps(
            {
                "fax_id": str(fax.uuid),
                "to": "+16175551234",
                "pdf_url": storage_item.file.url,
                "callback_url": f"some-url?token={fax.token}",
            }
        ),
        MessageGroupId="+16175551234",
    )


@pytest.mark.django_db
def test_send_fax_disabled(settings, mock_sqs_client, mock_handle_callback, freezer):
    freezer.move_to("2009-01-20 11:30:00")

    settings.FAX_DISABLE = True
    settings.FAX_OVERRIDE_DEST = None
    settings.FAX_GATEWAY_SQS_QUEUE = "some-queue"
    settings.FAX_GATEWAY_CALLBACK_URL = "some-url"

    storage_item = baker.make_recipe("storage.ballot_request_form")

    send_fax(storage_item, "+16175551234", "some_task", "some_task_arg")

    fax = Fax.objects.get(storage_item=storage_item)

    assert not mock_sqs_client.called
    mock_handle_callback.assert_called_with(
        {
            "fax_id": fax.uuid,
            "message": "Simulated fax successful",
            "timestamp": datetime(2009, 1, 20, 11, 30, 0, tzinfo=timezone.utc),
            "status": FaxStatus.SENT,
        },
        fax,
    )


@pytest.mark.django_db
def test_send_fax_override(settings, mock_sqs_client):
    settings.FAX_DISABLE = True
    settings.FAX_OVERRIDE_DEST = "+16175556789"
    settings.FAX_GATEWAY_SQS_QUEUE = "some-queue"
    settings.FAX_GATEWAY_CALLBACK_URL = "some-url"

    storage_item = baker.make_recipe("storage.ballot_request_form")

    send_fax(storage_item, "+16175551234", "some_task", "some_task_arg")

    fax = Fax.objects.get(storage_item=storage_item)

    mock_sqs_client.send_message.assert_called_with(
        QueueUrl="some-queue",
        MessageBody=json.dumps(
            {
                "fax_id": str(fax.uuid),
                "to": "+16175556789",
                "pdf_url": storage_item.file.url,
                "callback_url": f"some-url?token={fax.token}",
            }
        ),
        MessageGroupId="+16175556789",
    )
