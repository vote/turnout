import datetime
import json
import os
from copy import copy

import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from common.enums import VoterStatus
from election.models import State
from multi_tenant.models import Client
from verifier.models import Lookup

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
}
EXPECTED_QUERYSTRING = {
    "first_name": ["Barack"],
    "last_name": ["Obama"],
    "dob": ["1961**"],
    "zip_code": ["60657"],
    "state": ["IL"],
    "unparsed_full_address": ["1600 Penn Avenue, Chicago, IL 60657"],
}
TARGETSMART_ENDPOINT = "https://api.targetsmart.com/voter/voter-registration-check"
SAMPLE_PROVIDER_RESPONSES_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "sample_provider_responses/")
)


def test_get_request_disallowed():
    client = APIClient()
    response = client.get(LOOKUP_API_ENDPOINT)
    assert response.status_code == 405
    assert response.json() == {"detail": 'Method "GET" not allowed.'}


def test_blank_api_request(requests_mock):
    client = APIClient()
    targetsmart_call = requests_mock.register_uri("GET", TARGETSMART_ENDPOINT)
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
    assert not targetsmart_call.called


@pytest.mark.django_db
def test_proper_targetsmart_request(requests_mock, settings):
    client = APIClient()
    targetsmart_call = requests_mock.register_uri(
        "GET", TARGETSMART_ENDPOINT, json={"result": [], "too_many": False},
    )

    settings.TARGETSMART_KEY = "mytargetsmartkey"
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.status_code == 200
    assert response.json() == {"registered": False}

    assert requests_mock.call_count == 1
    assert targetsmart_call.last_request.headers["x-api-key"] == "mytargetsmartkey"
    assert targetsmart_call.last_request.qs == EXPECTED_QUERYSTRING


@pytest.mark.django_db
def test_targetsmart_request_address2(requests_mock):
    client = APIClient()
    targetsmart_call = requests_mock.register_uri(
        "GET", TARGETSMART_ENDPOINT, json={"result": [], "too_many": False},
    )

    address2_lookup = copy(VALID_LOOKUP)
    address2_lookup["address2"] = "Unit 2008"
    response = client.post(LOOKUP_API_ENDPOINT, address2_lookup)
    assert response.status_code == 200
    assert response.json() == {"registered": False}

    address2_qs = copy(EXPECTED_QUERYSTRING)
    address2_qs["unparsed_full_address"] = [
        "1600 Penn Avenue Unit 2008, Chicago, IL 60657"
    ]
    assert targetsmart_call.last_request.qs == address2_qs


@pytest.mark.django_db
def test_lookup_object_created(requests_mock):
    client = APIClient()
    targetsmart_call = requests_mock.register_uri(
        "GET", TARGETSMART_ENDPOINT, json={"result": [], "too_many": False},
    )

    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.status_code == 200
    assert response.json() == {"registered": False}

    assert Lookup.objects.count() == 1
    lookup = Lookup.objects.first()

    assert lookup.first_name == "Barack"
    assert lookup.last_name == "Obama"
    assert lookup.address1 == "1600 Penn Avenue"
    assert lookup.city == "Chicago"
    assert lookup.state == State.objects.get(pk="IL")
    assert lookup.date_of_birth == datetime.date(year=1961, month=8, day=4)
    assert lookup.zipcode == "60657"
    assert lookup.phone.as_e164 == "+13129289292"
    assert lookup.response == {"result": [], "too_many": False}
    first_partner = Client.objects.first()
    assert lookup.partner == first_partner


@pytest.mark.django_db
def test_default_partner(requests_mock):
    client = APIClient()
    targetsmart_call = requests_mock.register_uri(
        "GET", TARGETSMART_ENDPOINT, json={"result": [], "too_many": False},
    )

    first_partner = Client.objects.first()
    baker.make_recipe("multi_tenant.client")
    assert Client.objects.count() == 2

    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.status_code == 200
    assert response.json() == {"registered": False}

    lookup = Lookup.objects.first()
    assert lookup.partner == first_partner


@pytest.mark.django_db
def test_custom_partner(requests_mock):
    client = APIClient()
    targetsmart_call = requests_mock.register_uri(
        "GET", TARGETSMART_ENDPOINT, json={"result": [], "too_many": False},
    )

    second_partner = baker.make_recipe("multi_tenant.client")
    assert Client.objects.count() == 2

    url = f"{LOOKUP_API_ENDPOINT}?partner={second_partner.pk}"
    response = client.post(url, VALID_LOOKUP)
    assert response.status_code == 200
    assert response.json() == {"registered": False}

    lookup = Lookup.objects.first()
    assert lookup.partner == second_partner


@pytest.mark.django_db
def test_invalid_partner_key(requests_mock):
    client = APIClient()
    targetsmart_call = requests_mock.register_uri(
        "GET", TARGETSMART_ENDPOINT, json={"result": [], "too_many": False},
    )

    first_partner = Client.objects.first()
    baker.make_recipe("multi_tenant.client")
    assert Client.objects.count() == 2

    url = f"{LOOKUP_API_ENDPOINT}?partner=INVALID"
    response = client.post(url, VALID_LOOKUP)
    assert response.status_code == 200
    assert response.json() == {"registered": False}

    lookup = Lookup.objects.first()
    assert lookup.partner == first_partner


def test_invalid_zipcode(requests_mock):
    client = APIClient()
    targetsmart_call = requests_mock.register_uri("GET", TARGETSMART_ENDPOINT)
    bad_zip_lookup = copy(VALID_LOOKUP)
    bad_zip_lookup["zipcode"] = "123"
    response = client.post(LOOKUP_API_ENDPOINT, bad_zip_lookup)
    assert response.status_code == 400
    assert response.json() == {"zipcode": ["Zip codes are 5 digits"]}
    assert not targetsmart_call.called


def test_invalid_phone(requests_mock):
    client = APIClient()
    targetsmart_call = requests_mock.register_uri("GET", TARGETSMART_ENDPOINT)
    bad_phone_lookup = copy(VALID_LOOKUP)
    bad_phone_lookup["phone"] = "123"
    response = client.post(LOOKUP_API_ENDPOINT, bad_phone_lookup)
    assert response.status_code == 400
    assert response.json() == {"phone": ["Enter a valid phone number."]}
    assert not targetsmart_call.called


def test_invalid_state(requests_mock):
    client = APIClient()
    targetsmart_call = requests_mock.register_uri("GET", TARGETSMART_ENDPOINT)
    bad_state_lookup = copy(VALID_LOOKUP)
    bad_state_lookup["state"] = "ZZ"
    response = client.post(LOOKUP_API_ENDPOINT, bad_state_lookup)
    assert response.status_code == 400
    assert response.json() == {"state": ['"ZZ" is not a valid choice.']}
    assert not targetsmart_call.called


def test_provider_response_500_error(requests_mock):
    client = APIClient()
    requests_mock.register_uri(
        "GET", TARGETSMART_ENDPOINT, status_code=500, text="ERROR"
    )
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.status_code == 503
    assert response.json() == {"error": "Error from data provider"}


def test_provider_response_missing_parameters(requests_mock):
    client = APIClient()
    with open(
        os.path.join(SAMPLE_PROVIDER_RESPONSES_PATH, "missing_required_parameters.json")
    ) as json_file:
        data = json.load(json_file)
    requests_mock.register_uri("GET", TARGETSMART_ENDPOINT, status_code=400, json=data)
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.status_code == 503
    assert response.json() == {"error": "Error from data provider"}


def test_provider_response_bad_character(requests_mock):
    client = APIClient()
    with open(
        os.path.join(SAMPLE_PROVIDER_RESPONSES_PATH, "bad_character_error.json")
    ) as json_file:
        data = json.load(json_file)
    requests_mock.register_uri("GET", TARGETSMART_ENDPOINT, status_code=400, json=data)
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.status_code == 503
    assert response.json() == {"error": "Error from data provider"}


@pytest.mark.django_db
def test_provider_response_voter_not_found(requests_mock):
    client = APIClient()
    with open(
        os.path.join(SAMPLE_PROVIDER_RESPONSES_PATH, "not_found.json")
    ) as json_file:
        data = json.load(json_file)

    requests_mock.register_uri("GET", TARGETSMART_ENDPOINT, json=data)
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.json() == {"registered": False}
    lookup = Lookup.objects.first()
    assert lookup.response == data
    assert lookup.too_many == False
    assert lookup.registered == False
    assert not lookup.voter_status


@pytest.mark.django_db
def test_provider_response_active_voter(requests_mock):
    client = APIClient()
    with open(os.path.join(SAMPLE_PROVIDER_RESPONSES_PATH, "active.json")) as json_file:
        data = json.load(json_file)
    requests_mock.register_uri("GET", TARGETSMART_ENDPOINT, json=data)
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.json() == {"registered": True}
    lookup = Lookup.objects.first()
    assert lookup.response == data
    assert lookup.too_many == False
    assert lookup.registered == True
    assert lookup.voter_status == VoterStatus.ACTIVE


@pytest.mark.django_db
def test_provider_response_inactive_voter(requests_mock):
    client = APIClient()
    with open(
        os.path.join(SAMPLE_PROVIDER_RESPONSES_PATH, "inactive.json")
    ) as json_file:
        data = json.load(json_file)
    requests_mock.register_uri("GET", TARGETSMART_ENDPOINT, json=data)
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.json() == {"registered": False}
    lookup = Lookup.objects.first()
    assert lookup.response == data
    assert lookup.too_many == False
    assert lookup.registered == False
    assert lookup.voter_status == VoterStatus.INACTIVE


@pytest.mark.django_db
def test_provider_response_unknown_voter(requests_mock):
    client = APIClient()
    with open(
        os.path.join(SAMPLE_PROVIDER_RESPONSES_PATH, "unknown.json")
    ) as json_file:
        data = json.load(json_file)
    requests_mock.register_uri("GET", TARGETSMART_ENDPOINT, json=data)
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.json() == {"registered": False}
    lookup = Lookup.objects.first()
    assert lookup.response == data
    assert lookup.too_many == False
    assert lookup.registered == False
    assert lookup.voter_status == VoterStatus.UNKNOWN


@pytest.mark.django_db
def test_provider_response_too_many(requests_mock):
    client = APIClient()
    with open(
        os.path.join(SAMPLE_PROVIDER_RESPONSES_PATH, "too_many.json")
    ) as json_file:
        data = json.load(json_file)
    requests_mock.register_uri("GET", TARGETSMART_ENDPOINT, json=data)
    response = client.post(LOOKUP_API_ENDPOINT, VALID_LOOKUP)
    assert response.json() == {"registered": False}
    lookup = Lookup.objects.first()
    assert lookup.response == data
    assert lookup.too_many == True
    assert lookup.registered == False
