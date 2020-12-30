import datetime
import json
import os
from base64 import b64encode
from copy import copy
from uuid import UUID

import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from action.models import Action
from common.enums import EventType, SubscriberStatus, VoterStatus
from election.models import State
from event_tracking.models import Event
from multi_tenant.models import Client
from verifier.alloy import ALLOY_ENDPOINT, query_alloy
from verifier.models import Lookup
from verifier.serializers import LookupSerializer
from verifier.targetsmart import TARGETSMART_ENDPOINT, query_targetsmart

LOOKUP_API_ENDPOINT = "/v1/verification/verify/"
VALID_LOOKUP = {
    "first_name": "Barack",
    "last_name": "Obama",
    "address1": "1600 Penn Avenue",
    "city": "Chicago",
    "state": "IL",
    "email": "barack@barackobama.local",
    "date_of_birth": "1961-08-04",
    "zipcode": "60657",
    "phone": "+13129289292",
    "sms_opt_in_subscriber": False,
    "source": "mysource",
    "utm_campaign": "mycampaign",
    "utm_medium": "test",
    "utm_source": "django",
    "utm_content": "this-is-a-test",
    "utm_term": "voteamerica",
    "session_id": "7293d330-3216-439b-aa1a-449c7c458ebe",
    "email_referrer": "abcd123",
    "mobile_referrer": "efgh456",
    "embed_url": "https://www.greatvoter.com/location/of/embed?secret_data=here",
}
TARGETSMART_EXPECTED_QUERYSTRING = {
    "first_name": ["Barack"],
    "last_name": ["Obama"],
    "dob": ["1961*"],
    "zip_code": ["60657"],
    "state": ["IL"],
    "unparsed_full_address": ["1600 Penn Avenue, Chicago, IL 60657"],
}
ALLOY_EXPECTED_QUERYSTRING = {
    "first_name": ["Barack"],
    "last_name": ["Obama"],
    "birth_date": ["1961-08-04"],
    "address": ["1600 Penn Avenue"],
    "city": ["Chicago"],
    "state": ["IL"],
    "zip": ["60657"],
}
TARGETSMART_RESPONSES_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "sample_targetsmart_responses/")
)
ALLOY_RESPONSES_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "sample_alloy_responses/")
)


def load_alloy(filename):
    with open(os.path.join(ALLOY_RESPONSES_PATH, filename)) as json_file:
        data = json.load(json_file)
    return data


def load_targetsmart(filename):
    with open(os.path.join(TARGETSMART_RESPONSES_PATH, filename)) as json_file:
        data = json.load(json_file)
    return data


@pytest.fixture()
def mock_apicalls(mocker):
    mocker.patch("verifier.api_views.gevent.joinall", return_value=None)

    def process_calls(alloy_data, targetsmart_data):
        alloy_response = mocker.Mock()
        alloy_response.value = alloy_data
        targetsmart_response = mocker.Mock()
        targetsmart_response.value = targetsmart_data
        mocker.patch(
            "verifier.api_views.gevent.spawn",
            side_effect=[alloy_response, targetsmart_response],
        )

    return process_calls


@pytest.fixture(autouse=True)
def mock_cache(mocker):
    mocker.patch("verifier.alloy.cache.get", return_value=None)
    mocker.patch("verifier.alloy.cache.set", return_value=None)


@pytest.fixture(autouse=True)
def apikey_override(settings):
    settings.TARGETSMART_KEY = "mytargetsmartkey"
    settings.ALLOY_KEY = "myalloykey"
    settings.ALLOY_SECRET = "myalloysecret"
    settings.ACTIONNETWORK_SYNC = False


@pytest.fixture()
def mock_finish(settings, mocker):
    return mocker.patch("verifier.api_views.action_finish.delay")


def test_get_request_disallowed():
    client = APIClient()
    response = client.get(LOOKUP_API_ENDPOINT)
    assert response.status_code == 405
    assert response.json() == {"detail": 'Method "GET" not allowed.'}


def test_blank_api_request():
    client = APIClient()
    response = client.post(LOOKUP_API_ENDPOINT, {})
    assert response.status_code == 400
    expected_response = {
        "first_name": ["This field is required."],
        "last_name": ["This field is required."],
        "address1": ["This field is required."],
        "city": ["This field is required."],
        "zipcode": ["This field is required."],
        "state": ["This field is required."],
        "email": ["This field is required."],
        "date_of_birth": ["This field is required."],
    }
    assert response.json() == expected_response


def test_proper_api_calls(requests_mock):
    targetsmart_data = load_targetsmart("active.json")
    targetsmart_call = requests_mock.register_uri(
        "GET", TARGETSMART_ENDPOINT, json=targetsmart_data
    )
    alloy_data = load_alloy("active.json")
    alloy_call = requests_mock.register_uri("GET", ALLOY_ENDPOINT, json=alloy_data)

    serializer = LookupSerializer(data=VALID_LOOKUP)
    serializer.is_valid()

    alloy_result = query_alloy(serializer.validated_data)
    targetsmart_result = query_targetsmart(serializer.validated_data)

    assert alloy_result == alloy_data
    assert targetsmart_result == targetsmart_data

    alloy_auth_string = (
        "Basic " + b64encode("myalloykey:myalloysecret".encode()).decode()
    )
    assert alloy_call.last_request.headers["authorization"] == alloy_auth_string
    assert alloy_call.last_request.qs == ALLOY_EXPECTED_QUERYSTRING

    assert targetsmart_call.last_request.headers["x-api-key"] == "mytargetsmartkey"
    assert targetsmart_call.last_request.qs == TARGETSMART_EXPECTED_QUERYSTRING


@pytest.mark.django_db
def test_lookup_created(requests_mock, mock_finish, mock_apicalls):
    client = APIClient()
    targetsmart_response_data = load_targetsmart("active.json")
    alloy_response_data = load_alloy("active.json")
    mock_apicalls(alloy_response_data, targetsmart_response_data)

    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.status_code == 200
    lookup = Lookup.objects.first()
    assert response.json() == {"registered": True, "action_id": str(lookup.action.pk)}

    assert lookup.first_name == "Barack"
    assert lookup.last_name == "Obama"
    assert lookup.address1 == "1600 Penn Avenue"
    assert lookup.city == "Chicago"
    assert lookup.state == State.objects.get(pk="IL")
    assert lookup.date_of_birth == datetime.date(year=1961, month=8, day=4)
    assert lookup.zipcode == "60657"
    assert lookup.phone.as_e164 == "+13129289292"
    assert lookup.sms_opt_in_subscriber == False
    assert lookup.alloy_response == alloy_response_data
    assert lookup.alloy_status == VoterStatus.ACTIVE
    assert lookup.targetsmart_response == targetsmart_response_data
    assert lookup.targetsmart_status == VoterStatus.ACTIVE
    action = Action.objects.first()
    assert lookup.action == action
    assert lookup.session_id == UUID("7293d330-3216-439b-aa1a-449c7c458ebe")
    first_subscriber = Client.objects.first()
    assert lookup.subscriber == first_subscriber
    assert (
        Event.objects.filter(action=lookup.action, event_type=EventType.FINISH).count()
        == 1
    )


@pytest.mark.django_db
def test_mismatch_a_active_ts_not_found(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("active.json"), load_targetsmart("not_found.json"))
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    lookup = Lookup.objects.first()
    assert response.json() == {"registered": True, "action_id": str(lookup.action.pk)}
    assert lookup.targetsmart_status == VoterStatus.UNKNOWN
    assert lookup.alloy_status == VoterStatus.ACTIVE
    assert lookup.voter_status == VoterStatus.ACTIVE
    assert lookup.registered == True


@pytest.mark.django_db
def test_mismatch_ts_active_a_not_found(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("not_found.json"), load_targetsmart("active.json"))
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    lookup = Lookup.objects.first()
    assert response.json() == {"registered": True, "action_id": str(lookup.action.pk)}
    assert lookup.targetsmart_status == VoterStatus.ACTIVE
    assert lookup.alloy_status == VoterStatus.UNKNOWN
    assert lookup.voter_status == VoterStatus.ACTIVE
    assert lookup.registered == True


@pytest.mark.django_db
def test_mismatch_ts_active_a_inactive(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("inactive.json"), load_targetsmart("active.json"))
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    lookup = Lookup.objects.first()
    assert response.json() == {"registered": False, "action_id": str(lookup.action.pk)}
    assert lookup.targetsmart_status == VoterStatus.ACTIVE
    assert lookup.alloy_status == VoterStatus.INACTIVE
    assert lookup.voter_status == VoterStatus.INACTIVE
    assert lookup.registered == False


@pytest.mark.django_db
def test_dual_match(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("active.json"), load_targetsmart("active.json"))
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    lookup = Lookup.objects.first()
    assert response.json() == {"registered": True, "action_id": str(lookup.action.pk)}
    assert lookup.targetsmart_status == VoterStatus.ACTIVE
    assert lookup.alloy_status == VoterStatus.ACTIVE
    assert lookup.voter_status == VoterStatus.ACTIVE
    assert lookup.registered == True


@pytest.mark.django_db
def test_ts_too_many(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("active.json"), load_targetsmart("too_many.json"))
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    lookup = Lookup.objects.first()
    assert response.json() == {"registered": True, "action_id": str(lookup.action.pk)}
    assert lookup.targetsmart_status == VoterStatus.UNKNOWN
    assert lookup.alloy_status == VoterStatus.ACTIVE
    assert lookup.voter_status == VoterStatus.ACTIVE
    assert lookup.registered == True


@pytest.mark.django_db
def test_not_found(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("not_found.json"), load_targetsmart("not_found.json"))
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    lookup = Lookup.objects.first()
    assert response.json() == {"registered": False, "action_id": str(lookup.action.pk)}
    assert lookup.targetsmart_status == VoterStatus.UNKNOWN
    assert lookup.alloy_status == VoterStatus.UNKNOWN
    assert lookup.voter_status == VoterStatus.UNKNOWN
    assert lookup.registered == False


@pytest.mark.django_db
def test_ts_error(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(
        load_alloy("active.json"), load_targetsmart("bad_character_error.json")
    )
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    lookup = Lookup.objects.first()
    assert response.json() == {"registered": True, "action_id": str(lookup.action.pk)}
    assert lookup.targetsmart_status == VoterStatus.UNKNOWN
    assert lookup.alloy_status == VoterStatus.ACTIVE
    assert lookup.voter_status == VoterStatus.ACTIVE
    assert lookup.registered == True


@pytest.mark.django_db
def test_dual_error(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls({"error": "Boo"}, {"error": "No!!!"})
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.status_code == 503
    assert response.json() == {"error": "Error from data providers"}
    assert Lookup.objects.count() == 0


@pytest.mark.django_db
def test_finish(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("active.json"), load_targetsmart("active.json"))

    client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)

    mock_finish.assert_called_once()


@pytest.mark.django_db
def test_sourcing(mock_apicalls, mocker, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("active.json"), load_targetsmart("active.json"))

    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.status_code == 200

    assert Lookup.objects.count() == 1
    lookup = Lookup.objects.first()

    assert lookup.source == "mysource"
    assert lookup.utm_campaign == "mycampaign"
    assert lookup.utm_medium == "test"
    assert lookup.utm_source == "django"
    assert lookup.utm_content == "this-is-a-test"
    assert lookup.utm_term == "voteamerica"
    assert lookup.email_referrer == "abcd123"
    assert lookup.mobile_referrer == "efgh456"
    assert lookup.embed_url == "https://www.greatvoter.com/location/of/embed"


@pytest.mark.django_db
def test_default_subscriber(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("active.json"), load_targetsmart("active.json"))

    first_subscriber = Client.objects.first()
    baker.make_recipe("multi_tenant.client")
    assert Client.objects.count() == 4

    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.status_code == 200
    action = Action.objects.first()
    assert response.json() == {"registered": True, "action_id": str(action.pk)}

    lookup = Lookup.objects.first()
    assert lookup.subscriber == first_subscriber


@pytest.mark.django_db
def test_inactive_subscriber(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("active.json"), load_targetsmart("active.json"))

    first_subscriber = Client.objects.first()
    second_subscriber = baker.make_recipe("multi_tenant.client")
    baker.make_recipe(
        "multi_tenant.subscriberslug",
        subscriber=second_subscriber,
        slug="verifierslugtwo",
    )
    assert Client.objects.count() == 4

    mock_apicalls(load_alloy("active.json"), load_targetsmart("active.json"))

    url = f"{LOOKUP_API_ENDPOINT}?subscriber=verifierslugtwo"
    response = client.post(url, VALID_LOOKUP)
    assert response.status_code == 200
    action = Action.objects.first()
    assert response.json() == {"registered": True, "action_id": str(action.pk)}

    lookup = Lookup.objects.first()
    assert lookup.subscriber == second_subscriber

    # Set the second subscriber to disabled and try another verification
    second_subscriber.status = SubscriberStatus.DISABLED
    second_subscriber.save()

    mock_apicalls(load_alloy("active.json"), load_targetsmart("active.json"))

    inactive_subscriber_response = client.post(url, VALID_LOOKUP)
    assert inactive_subscriber_response.status_code == 200

    assert Lookup.objects.count() == 2
    inactive_lookup = Lookup.objects.first()
    assert inactive_subscriber_response.json() == {
        "registered": True,
        "action_id": str(inactive_lookup.action.pk),
    }
    assert inactive_lookup.subscriber == first_subscriber


@pytest.mark.django_db
def test_custom_subscriber(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("active.json"), load_targetsmart("active.json"))

    second_subscriber = baker.make_recipe("multi_tenant.client")
    baker.make_recipe(
        "multi_tenant.subscriberslug",
        subscriber=second_subscriber,
        slug="verifierslugtwo",
    )
    assert Client.objects.count() == 4

    url = f"{LOOKUP_API_ENDPOINT}?subscriber=verifierslugtwo"
    response = client.post(url, VALID_LOOKUP)
    assert response.status_code == 200
    action = Action.objects.first()
    assert response.json() == {"registered": True, "action_id": str(action.pk)}

    lookup = Lookup.objects.first()
    assert lookup.subscriber == second_subscriber


@pytest.mark.django_db
def test_invalid_subscriber_key(mock_apicalls, mock_finish):
    client = APIClient()
    mock_apicalls(load_alloy("active.json"), load_targetsmart("active.json"))

    first_subscriber = Client.objects.first()
    second_subscriber = baker.make_recipe("multi_tenant.client")
    baker.make_recipe("multi_tenant.subscriberslug", subscriber=second_subscriber)
    assert Client.objects.count() == 4

    url = f"{LOOKUP_API_ENDPOINT}?subscriber=INVALID"
    response = client.post(url, VALID_LOOKUP)
    assert response.status_code == 200
    action = Action.objects.first()
    assert response.json() == {"registered": True, "action_id": str(action.pk)}

    lookup = Lookup.objects.first()
    assert lookup.subscriber == first_subscriber


def test_invalid_zipcode():
    client = APIClient()
    bad_zip_lookup = copy(VALID_LOOKUP)
    bad_zip_lookup["zipcode"] = "123"
    response = client.post(LOOKUP_API_ENDPOINT, bad_zip_lookup)
    assert response.status_code == 400
    assert response.json() == {"zipcode": ["Zip codes are 5 digits"]}


def test_invalid_phone():
    client = APIClient()
    bad_phone_lookup = copy(VALID_LOOKUP)
    bad_phone_lookup["phone"] = "123"
    response = client.post(LOOKUP_API_ENDPOINT, bad_phone_lookup)
    assert response.status_code == 400
    assert response.json() == {"phone": ["Enter a valid phone number."]}


def test_invalid_state():
    client = APIClient()
    bad_state_lookup = copy(VALID_LOOKUP)
    bad_state_lookup["state"] = "ZZ"
    response = client.post(LOOKUP_API_ENDPOINT, bad_state_lookup)
    assert response.status_code == 400
    assert response.json() == {"state": ['"ZZ" is not a valid choice.']}
