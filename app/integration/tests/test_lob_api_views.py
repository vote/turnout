import json

import pytest
from django.conf import settings
from model_bakery import baker
from rest_framework.test import APIClient

from common.enums import (
    EventType,
    StateFieldFormats,
    SubmissionType,
    TurnoutActionStatus,
)
from event_tracking.models import Event

LOB_LETTER_STATUS_API_ENDPOINT = "/v1/integration/lob-letter-status/{uuid}/"

LOB_LETTER_STATUS_BODY = {
    "id": "evt_d95ff8ffd2b5cfb4",
    "body": {"id": "psc_d2d10a2e9cba991c", "blah": "blah",},
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
@pytest.mark.django_db
def test_lob_letter_status():
    import hashlib
    import hmac
    import base64

    settings.LOB_LETTER_WEBHOOK_SECRET = "foo"

    ballot_request = baker.make_recipe("absentee.ballot_request")

    timestamp = "last tuesday"
    body = json.dumps(LOB_LETTER_STATUS_BODY)
    message = timestamp + "." + body
    secret = settings.LOB_LETTER_WEBHOOK_SECRET
    signature = base64.b64encode(
        hmac.new(
            secret.encode("utf-8"), message.encode("utf-8"), digestmod=hashlib.sha256
        ).digest()
    )

    client = APIClient()
    response = client.post(
        LOB_LETTER_STATUS_API_ENDPOINT.format(uuid=ballot_request.action.uuid),
        body,
        content_type="application/json",
        **{"HTTP_LOB_SIGNATURE_TIMESTAMP": timestamp, "HTTP_LOB_SIGNATURE": signature,},
    )
    assert response.status_code == 200
    events = list(Event.objects.filter(action=ballot_request.action))
    assert len(events) == 1
    assert events[0].event_type == EventType.LOB_MAILED


# Test lob letter status callbacks
@pytest.mark.django_db
def test_lob_letter_status_bad_signature():
    import base64

    settings.LOB_LETTER_WEBHOOK_SECRET = "foo"

    ballot_request = baker.make_recipe("absentee.ballot_request")

    timestamp = "today"
    signature = base64.b64encode("not a valid hash value".encode("utf-8"))

    client = APIClient()
    response = client.post(
        LOB_LETTER_STATUS_API_ENDPOINT.format(uuid=ballot_request.action.uuid),
        json=LOB_LETTER_STATUS_BODY,
        **{
            "HTTP_X_LOB_SIGNATURE_TIMESTAMP": timestamp,
            "HTTP_X_LOB_SIGNATURE": signature,
        },
    )
    assert response.status_code == 403
