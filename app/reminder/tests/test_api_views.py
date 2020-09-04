import datetime
from uuid import UUID

import pytest
from rest_framework.test import APIClient

from action.models import Action
from election.models import State
from multi_tenant.models import Client
from reminder.models import ReminderRequest

SIGNUP_API_ENDPOINT = "/v1/reminder/signup/"
VALID_SIGNUP = {
    "first_name": "Barack",
    "last_name": "Obama",
    "address1": "1600 Penn Avenue",
    "city": "Chicago",
    "state": "IL",
    "email": "barack@barackobama.local",
    "date_of_birth": "1961-08-04",
    "zipcode": "60657",
    "phone": "+13129289292",
    "sms_opt_in": True,
    "sms_opt_in_subscriber": False,
    "source": "mysource",
    "utm_campaign": "mycampaign",
    "utm_medium": "test",
    "utm_source": "django",
    "utm_content": "this-is-a-test",
    "utm_term": "voteamerica",
    "session_id": "7293d330-3216-439b-aa1a-449c7c458ebe",
    "embed_url": "https://www.greatvoter.com/location/of/embed?secret_data=here",
    "email_referrer": "abcd123",
    "mobile_referrer": "efgh456",
}


@pytest.fixture
def mock_followup(mocker):
    return mocker.patch("reminder.api_views.action_finish")


def test_get_request_disallowed():
    client = APIClient()
    response = client.get(SIGNUP_API_ENDPOINT)
    assert response.status_code == 405
    assert response.json() == {"detail": 'Method "GET" not allowed.'}


def test_blank_api_request(requests_mock):
    client = APIClient()
    response = client.post(SIGNUP_API_ENDPOINT, {})
    assert response.status_code == 400
    expected_response = {
        "first_name": ["This field is required."],
        "last_name": ["This field is required."],
        "address1": ["This field is required."],
        "city": ["This field is required."],
        "state": ["This field is required."],
        "zipcode": ["This field is required."],
        "date_of_birth": ["This field is required."],
        "email": ["This field is required."],
    }
    assert response.json() == expected_response


@pytest.mark.django_db
def test_reminder_object_created(mocker, mock_followup):
    client = APIClient()
    response = client.post(SIGNUP_API_ENDPOINT, VALID_SIGNUP)
    assert response.status_code == 200
    action = Action.objects.first()
    assert response.json() == {"action_id": str(action.pk)}

    assert ReminderRequest.objects.count() == 1
    reminder_request = ReminderRequest.objects.first()

    assert reminder_request.first_name == "Barack"
    assert reminder_request.last_name == "Obama"
    assert reminder_request.address1 == "1600 Penn Avenue"
    assert reminder_request.city == "Chicago"
    assert reminder_request.state == State.objects.get(pk="IL")
    assert reminder_request.date_of_birth == datetime.date(year=1961, month=8, day=4)
    assert reminder_request.zipcode == "60657"
    assert reminder_request.phone.as_e164 == "+13129289292"
    assert reminder_request.sms_opt_in == True
    assert reminder_request.sms_opt_in_subscriber == False
    assert reminder_request.embed_url == "https://www.greatvoter.com/location/of/embed"
    assert reminder_request.session_id == UUID("7293d330-3216-439b-aa1a-449c7c458ebe")
    first_subscriber = Client.objects.first()
    assert reminder_request.subscriber == first_subscriber
