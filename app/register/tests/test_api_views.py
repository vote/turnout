import datetime
from copy import copy

import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from action.models import Action
from common.enums import (
    PersonTitle,
    PoliticalParties,
    RaceEthnicity,
    TurnoutActionStatus,
)
from election.models import State
from multi_tenant.models import Client
from register.api_views import RegistrationViewSet
from register.models import Registration

REGISTER_API_ENDPOINT = "/v1/registration/register/"
VALID_REGISTRATION = {
    "title": "Mr",
    "first_name": "John",
    "last_name": "Hancock",
    "address1": "30 Beacon Street",
    "city": "Boston",
    "state": "MA",
    "previous_address1": "133 Franklin St",
    "previous_city": "Quincy",
    "previous_state": "MA",
    "previous_zipcode": "02169",
    "email": "john@hancock.local",
    "date_of_birth": "1737-01-23",
    "zipcode": "02108",
    "phone": "+16174567890",
    "sms_opt_in": True,
    "us_citizen": True,
    "is_18_or_over": True,
    "state_id_number": "FOUNDER123",
    "party": "Other",
    "race_ethnicity": "White",
}
REGISTER_API_ENDPOINT_INCOMPLETE = "/v1/registration/register/?incomplete=true"

STATUS_API_ENDPOINT = "/v1/registration/status/{uuid}/"
STATUS_REFER_OVR = {"status": "ReferOVR"}


@pytest.fixture()
def submission_task_patch(mocker):
    return mocker.patch.object(RegistrationViewSet, "task")


def test_get_request_disallowed():
    client = APIClient()
    response = client.get(REGISTER_API_ENDPOINT)
    assert response.status_code == 405
    assert response.json() == {"detail": 'Method "GET" not allowed.'}


def test_blank_api_request():
    client = APIClient()
    response = client.post(REGISTER_API_ENDPOINT, {})
    assert response.status_code == 400
    expected_response = {
        "title": ["This field is required."],
        "first_name": ["This field is required."],
        "last_name": ["This field is required."],
        "address1": ["This field is required."],
        "city": ["This field is required."],
        "zipcode": ["This field is required."],
        "state": ["This field is required."],
        "email": ["This field is required."],
        "date_of_birth": ["This field is required."],
        "us_citizen": ["This field is required."],
        "is_18_or_over": ["This field is required."],
        "state_id_number": ["This field is required."],
    }
    assert response.json() == expected_response


@pytest.mark.django_db
def test_register_object_created(submission_task_patch):
    client = APIClient()

    response = client.post(REGISTER_API_ENDPOINT, VALID_REGISTRATION)
    assert response.status_code == 200
    assert "uuid" in response.json()

    assert Registration.objects.count() == 1
    registration = Registration.objects.first()
    assert response.json()["uuid"] == str(registration.uuid)

    assert registration.title == PersonTitle.MR
    assert registration.first_name == "John"
    assert registration.last_name == "Hancock"
    assert registration.address1 == "30 Beacon Street"
    assert registration.city == "Boston"
    assert registration.state == State.objects.get(pk="MA")
    assert registration.zipcode == "02108"
    assert registration.previous_address1 == "133 Franklin St"
    assert registration.previous_city == "Quincy"
    assert registration.previous_state == State.objects.get(pk="MA")
    assert registration.previous_zipcode == "02169"
    assert registration.date_of_birth == datetime.date(year=1737, month=1, day=23)
    assert registration.phone.as_e164 == "+16174567890"
    assert registration.sms_opt_in == True
    assert registration.us_citizen == True
    assert registration.party == PoliticalParties.OTHER
    assert registration.race_ethnicity == RaceEthnicity.WHITE
    assert registration.status == TurnoutActionStatus.PENDING
    assert registration.action == Action.objects.first()

    first_partner = Client.objects.first()
    assert registration.partner == first_partner

    submission_task_patch.delay.assert_called_once_with(
        registration.uuid, "FOUNDER123", True
    )


@pytest.mark.django_db
def test_default_partner(submission_task_patch):
    client = APIClient()

    first_partner = Client.objects.first()
    baker.make_recipe("multi_tenant.client")
    assert Client.objects.count() == 2

    response = client.post(REGISTER_API_ENDPOINT, VALID_REGISTRATION)
    assert response.status_code == 200
    assert "uuid" in response.json()

    registration = Registration.objects.first()
    assert response.json()["uuid"] == str(registration.uuid)
    assert registration.partner == first_partner

    submission_task_patch.delay.assert_called_once_with(
        registration.uuid, "FOUNDER123", True
    )


@pytest.mark.django_db
def test_custom_partner(submission_task_patch):
    client = APIClient()

    second_partner = baker.make_recipe("multi_tenant.client")
    baker.make_recipe(
        "multi_tenant.partnerslug", partner=second_partner, slug="custompartertwoslug"
    )
    assert Client.objects.count() == 2

    url = f"{REGISTER_API_ENDPOINT}?partner=custompartertwoslug"
    response = client.post(url, VALID_REGISTRATION)
    assert response.status_code == 200
    assert "uuid" in response.json()

    registration = Registration.objects.first()
    assert response.json()["uuid"] == str(registration.uuid)
    assert registration.partner == second_partner

    submission_task_patch.delay.assert_called_once_with(
        registration.uuid, "FOUNDER123", True
    )


@pytest.mark.django_db
def test_invalid_partner_key(submission_task_patch):
    client = APIClient()

    first_partner = Client.objects.first()
    second_partner = baker.make_recipe("multi_tenant.client")
    baker.make_recipe("multi_tenant.partnerslug", partner=second_partner)
    assert Client.objects.count() == 2

    url = f"{REGISTER_API_ENDPOINT}?partner=INVALID"
    response = client.post(url, VALID_REGISTRATION)
    assert response.status_code == 200
    assert "uuid" in response.json()

    registration = Registration.objects.first()
    assert response.json()["uuid"] == str(registration.uuid)
    assert registration.partner == first_partner

    submission_task_patch.delay.assert_called_once_with(
        registration.uuid, "FOUNDER123", True
    )


def test_not_us_citizen():
    client = APIClient()
    not_citzen_register = copy(VALID_REGISTRATION)
    not_citzen_register["us_citizen"] = False
    response = client.post(REGISTER_API_ENDPOINT, not_citzen_register)
    assert response.status_code == 400
    assert response.json() == {"us_citizen": ["Must be true"]}


def test_not_18_or_over():
    client = APIClient()
    not_18_years_old_register = copy(VALID_REGISTRATION)
    not_18_years_old_register["is_18_or_over"] = False
    response = client.post(REGISTER_API_ENDPOINT, not_18_years_old_register)
    assert response.status_code == 400
    assert response.json() == {"is_18_or_over": ["Must be true"]}


def test_invalid_zipcode():
    client = APIClient()
    bad_zip_register = copy(VALID_REGISTRATION)
    bad_zip_register["zipcode"] = "123"
    response = client.post(REGISTER_API_ENDPOINT, bad_zip_register)
    assert response.status_code == 400
    assert response.json() == {"zipcode": ["Zip codes are 5 digits"]}


def test_invalid_phone():
    client = APIClient()
    bad_phone_register = copy(VALID_REGISTRATION)
    bad_phone_register["phone"] = "123"
    response = client.post(REGISTER_API_ENDPOINT, bad_phone_register)
    assert response.status_code == 400
    assert response.json() == {"phone": ["Enter a valid phone number."]}


def test_invalid_state():
    client = APIClient()
    bad_state_register = copy(VALID_REGISTRATION)
    bad_state_register["state"] = "ZZ"
    response = client.post(REGISTER_API_ENDPOINT, bad_state_register)
    assert response.status_code == 400
    assert response.json() == {"state": ['"ZZ" is not a valid choice.']}


@pytest.mark.django_db
def test_update_status():
    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE, VALID_REGISTRATION
    )
    assert register_response.status_code == 200
    assert "uuid" in register_response.json()

    registration = Registration.objects.first()
    assert register_response.json()["uuid"] == str(registration.uuid)
    assert registration.status == TurnoutActionStatus.INCOMPLETE

    status_api_url = STATUS_API_ENDPOINT.format(uuid=registration.uuid)
    status_response = client.patch(status_api_url, STATUS_REFER_OVR)
    assert status_response.status_code == 200
    assert status_response.json() == STATUS_REFER_OVR

    # refresh from database, make sure it's the same object
    registration.refresh_from_db()
    assert str(registration.uuid) == register_response.json()["uuid"]
    assert registration.status == TurnoutActionStatus.OVR_REFERRED


@pytest.mark.django_db
def test_invalid_update_status():
    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE, VALID_REGISTRATION
    )
    assert register_response.status_code == 200
    assert "uuid" in register_response.json()

    registration = Registration.objects.first()
    assert register_response.json()["uuid"] == str(registration.uuid)
    assert registration.status == TurnoutActionStatus.INCOMPLETE

    invalid_update_status = copy(STATUS_REFER_OVR)
    invalid_update_status["status"] = "Invalid"

    status_api_url = STATUS_API_ENDPOINT.format(uuid=registration.uuid)
    status_response = client.patch(status_api_url, invalid_update_status)
    assert status_response.status_code == 400
    assert status_response.json() == {"status": ['"Invalid" is not a valid choice.']}
    assert registration.status == TurnoutActionStatus.INCOMPLETE


@pytest.mark.django_db
def test_bad_update_status():
    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE, VALID_REGISTRATION
    )
    assert register_response.status_code == 200
    assert "uuid" in register_response.json()

    registration = Registration.objects.first()
    assert register_response.json()["uuid"] == str(registration.uuid)
    assert registration.status == TurnoutActionStatus.INCOMPLETE

    bad_update_status = copy(STATUS_REFER_OVR)
    bad_update_status["status"] = "SentPDF"

    status_api_url = STATUS_API_ENDPOINT.format(uuid=registration.uuid)
    status_response = client.patch(status_api_url, bad_update_status)
    assert status_response.status_code == 400
    assert status_response.json() == {
        "status": ["Registration status can only be ReferOVR"]
    }
    assert registration.status == TurnoutActionStatus.INCOMPLETE
