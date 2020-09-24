import json

import pytest
from django.conf import settings
from model_bakery import baker
from rest_framework.test import APIClient

from common.enums import (
    EventType,
    ExternalToolType,
    StateFieldFormats,
    SubmissionType,
    TurnoutActionStatus,
)
from event_tracking.models import Event
from integration.models import Link
from integration.tasks import process_lob_letter_status

LOB_LETTER_STATUS_API_ENDPOINT = "/v1/integration/lob-letter-status/"

LOB_LETTER_STATUS_BODY = {
    "id": "evt_d95ff8ffd2b5cfb4",
    "body": {"id": "ltr_d2d10a2e9cba991c", "blah": "blah",},
    "event_type": {
        "id": "letter.mailed",
        "enabled_for_test": True,
        "resource": "letters",
        "object": "event_type",
    },
    "date_created": "2016-12-04T22:50:08.180Z",
    "object": "event",
}


# Test lob letter status callbacks
def test_lob_letter_status(mocker):
    import hashlib
    import hmac

    process_patch = mocker.patch("integration.api_views.process_lob_letter_status")

    settings.LOB_LETTER_WEBHOOK_SECRET = "foo"

    ballot_request = baker.make_recipe("absentee.ballot_request")
    link = Link.objects.create(
        action=ballot_request.action,
        external_tool=ExternalToolType.LOB,
        external_id=LOB_LETTER_STATUS_BODY["body"]["id"],
    )

    timestamp = "last tuesday"
    body = json.dumps(LOB_LETTER_STATUS_BODY)
    message = timestamp + "." + body
    secret = settings.LOB_LETTER_WEBHOOK_SECRET
    signature = hmac.new(
        secret.encode("utf-8"), message.encode("utf-8"), digestmod=hashlib.sha256
    ).hexdigest()

    client = APIClient()
    response = client.post(
        LOB_LETTER_STATUS_API_ENDPOINT,
        body,
        content_type="application/json",
        **{"HTTP_LOB_SIGNATURE_TIMESTAMP": timestamp, "HTTP_LOB_SIGNATURE": signature,},
    )
    assert response.status_code == 200

    process_patch.assert_called_once_with(
        LOB_LETTER_STATUS_BODY["body"]["id"], LOB_LETTER_STATUS_BODY["event_type"]["id"]
    )


@pytest.mark.django_db
def test_lob_letter_status(mocker):
    ballot_request = baker.make_recipe("absentee.ballot_request")
    link = Link.objects.create(
        action=ballot_request.action,
        external_tool=ExternalToolType.LOB,
        external_id=LOB_LETTER_STATUS_BODY["body"]["id"],
    )

    process_lob_letter_status(
        LOB_LETTER_STATUS_BODY["body"]["id"], LOB_LETTER_STATUS_BODY["event_type"]["id"]
    )

    events = list(Event.objects.filter(action=ballot_request.action))
    assert len(events) == 1
    assert events[0].event_type == EventType.LOB_MAILED


@pytest.mark.django_db
def test_dup_lob_letter_status(mocker):
    ballot_request = baker.make_recipe("absentee.ballot_request")
    link = Link.objects.create(
        action=ballot_request.action,
        external_tool=ExternalToolType.LOB,
        external_id=LOB_LETTER_STATUS_BODY["body"]["id"],
    )

    process_lob_letter_status(
        LOB_LETTER_STATUS_BODY["body"]["id"], LOB_LETTER_STATUS_BODY["event_type"]["id"]
    )
    process_lob_letter_status(
        LOB_LETTER_STATUS_BODY["body"]["id"], LOB_LETTER_STATUS_BODY["event_type"]["id"]
    )

    events = list(Event.objects.filter(action=ballot_request.action))
    assert len(events) == 1
    assert events[0].event_type == EventType.LOB_MAILED


# Test lob letter status callbacks
@pytest.mark.django_db
def test_lob_letter_status_bad_signature():
    settings.LOB_LETTER_WEBHOOK_SECRET = "foo"

    baker.make_recipe("absentee.ballot_request")

    timestamp = "today"
    signature = "abc123deadbeef"

    client = APIClient()
    response = client.post(
        LOB_LETTER_STATUS_API_ENDPOINT,
        json=LOB_LETTER_STATUS_BODY,
        **{
            "HTTP_X_LOB_SIGNATURE_TIMESTAMP": timestamp,
            "HTTP_X_LOB_SIGNATURE": signature,
        },
    )
    assert response.status_code == 403
