import datetime
from copy import copy
from uuid import UUID

import ovrlib
import pytest
from django.core.files.base import ContentFile
from model_bakery import baker
from rest_framework.test import APIClient
from smalluuid import SmallUUID

from action.models import Action
from common.enums import (
    EventType,
    PersonTitle,
    PoliticalParties,
    RaceEthnicity,
    SecureUploadType,
    TurnoutActionStatus,
)
from election.models import State
from event_tracking.models import Event
from integration.lob import generate_lob_token
from multi_tenant.models import Client
from register.models import Registration
from storage.models import SecureUploadItem

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
    "sms_opt_in_subscriber": True,
    "us_citizen": True,
    "is_18_or_over": True,
    "state_id_number": "FOUNDER123",
    "party": "Other",
    "race_ethnicity": "White",
    "session_id": "7293d330-3216-439b-aa1a-449c7c458ebe",
    "embed_url": "https://www.greatvoter.com/location/of/embed?secret_data=here",
    "email_referrer": "abcd123",
    "mobile_referrer": "efgh456",
}
REGISTER_API_ENDPOINT_INCOMPLETE = "/v1/registration/register/?incomplete=true"

VALID_PATCH_MAIL = {
    "us_citizen": True,
    "is_18_or_over": True,
    "state_id_number": "FOUNDER123",
    "request_mailing_address1": "123 A St NW foo",
    "request_mailing_city": "Washington",
    "request_mailing_state": "DC",
    "request_mailing_zipcode": "20001",
}

STATUS_API_ENDPOINT = "/v1/registration/status/{uuid}/"
STATUS_REFER_OVR = {"status": "ReferOVR"}

PATCH_API_ENDPOINT = "/v1/registration/register/{uuid}/"

PA_REGISTRATION_START = {
    "title": "Mrs.",
    "first_name": "Sally",
    "last_name": "Penndot",
    "address1": "123 a st",
    "city": "Clarion",
    "state": "PA",
    "zipcode": "16214",
    "date_of_birth": "1944-05-02",
    "email": "sage@newdream.net",
    "party": "Democratic",
    "gender": "Female",
    "state_fields": {},
}

PA_REGISTRATION_NODLSSNORSIG = {
    "us_citizen": True,
    "is_18_or_over": True,
    "declaration": True,
    "state_fields": {
        "region_id": 432147,
        "vbm_opt_in": False,
        "id_type": None,
        "federal_voter": False,
    },
}

PA_REGISTRATION_DL = {
    "us_citizen": True,
    "is_18_or_over": True,
    "declaration": True,
    "state_id_number": "99007069",
    "state_id_number_2": "1234",
    "party": "Other",
    "state_fields": {
        "region_id": 432147,
        "vbm_opt_in": False,
        "federal_voter": False,
        "party_other": "Foo",
    },
}

PA_REGISTRATION_SSN = {
    "us_citizen": True,
    "is_18_or_over": True,
    "declaration": True,
    "state_id_number_2": "1234",
    "state_fields": {"region_id": 432147, "vbm_opt_in": False, "federal_voter": False,},
}

PA_REGISTRATION_BADDL = {
    "us_citizen": True,
    "declaration": True,
    "is_18_or_over": True,
    "state_id_number": "12345678",
    "state_id_number_2": "1234",
    "state_fields": {"region_id": 432147, "vbm_opt_in": False, "federal_voter": False,},
}

PA_REGISTRATION_SIG = {
    "us_citizen": True,
    "is_18_or_over": True,
    "declaration": True,
    "state_id_number_2": "1234",
    "party": "None",
    "state_fields": {
        "region_id": 432147,
        "vbm_opt_in": False,
        "federal_voter": False,
        "signature": "...",
    },
}

LOB_LETTER_CONFIRM_API_ENDPOINT = (
    "/v1/registration/confirm-print-and-forward/{uuid}/?token={token}"
)


@pytest.fixture()
def mock_check_unfinished(mocker):
    return mocker.patch("register.api_views.action_check_unfinished")


@pytest.fixture()
def mock_upsell(mocker):
    return mocker.patch("register.event_hooks.external_tool_upsell.apply_async")


@pytest.fixture
def mock_verify_address(mocker):
    return mocker.patch("integration.lob.verify_address", return_value=(True, {}))


@pytest.fixture
def mock_finish(mocker):
    return mocker.patch("register.api_views.action_finish")


@pytest.fixture()
def submission_task_patch(mocker):
    return mocker.patch("register.api_views.process_registration")


def set_state_allow_print_and_forward(code):
    state = State.objects.get(code=code)
    state.allow_print_and_forward = True
    state.save()


@pytest.fixture()
def state_confirmation_email(mocker):
    return mocker.patch("register.pa.send_registration_state_confirmation.delay")


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
def test_register_object_created(
    submission_task_patch, mock_finish, mock_check_unfinished
):
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
    assert registration.sms_opt_in_subscriber == True
    assert registration.us_citizen == True
    assert registration.party == PoliticalParties.OTHER
    assert registration.race_ethnicity == RaceEthnicity.WHITE
    assert registration.status == TurnoutActionStatus.PENDING
    assert registration.action == Action.objects.first()
    assert registration.embed_url == "https://www.greatvoter.com/location/of/embed"
    assert registration.session_id == UUID("7293d330-3216-439b-aa1a-449c7c458ebe")
    assert registration.email_referrer == "abcd123"
    assert registration.mobile_referrer == "efgh456"

    first_subscriber = Client.objects.first()
    assert registration.subscriber == first_subscriber

    submission_task_patch.assert_called_once_with(registration, "FOUNDER123", True)
    mock_finish.delay.assert_called_once_with(registration.action.pk)


@pytest.mark.django_db
def test_non_url_embed_url(submission_task_patch, mock_check_unfinished, mock_finish):
    client = APIClient()

    new_valid_restration = copy(VALID_REGISTRATION)
    new_valid_restration["embed_url"] = "completely random non url string"

    response = client.post(REGISTER_API_ENDPOINT, new_valid_restration)
    assert response.status_code == 200
    assert "uuid" in response.json()

    registration = Registration.objects.first()
    assert registration.embed_url == "completely random non url string"
    mock_finish.delay.assert_called_once_with(registration.action.pk)


@pytest.mark.django_db
def test_default_subscriber(mock_check_unfinished, mock_finish, submission_task_patch):
    client = APIClient()

    first_subscriber = Client.objects.first()
    baker.make_recipe("multi_tenant.client")
    assert Client.objects.count() == 4

    response = client.post(REGISTER_API_ENDPOINT, VALID_REGISTRATION)
    assert response.status_code == 200
    assert "uuid" in response.json()

    registration = Registration.objects.first()
    assert response.json()["uuid"] == str(registration.uuid)
    assert registration.subscriber == first_subscriber

    submission_task_patch.assert_called_once_with(registration, "FOUNDER123", True)
    mock_finish.delay.assert_called_once_with(registration.action.pk)


@pytest.mark.django_db
def test_custom_subscriber(mock_check_unfinished, mock_finish, submission_task_patch):
    client = APIClient()

    second_subscriber = baker.make_recipe("multi_tenant.client")
    baker.make_recipe(
        "multi_tenant.subscriberslug",
        subscriber=second_subscriber,
        slug="custompartertwoslug",
    )
    assert Client.objects.count() == 4

    url = f"{REGISTER_API_ENDPOINT}?subscriber=custompartertwoslug"
    response = client.post(url, VALID_REGISTRATION)
    assert response.status_code == 200
    assert "uuid" in response.json()

    registration = Registration.objects.first()
    assert response.json()["uuid"] == str(registration.uuid)
    assert registration.subscriber == second_subscriber

    submission_task_patch.assert_called_once_with(registration, "FOUNDER123", True)
    mock_finish.delay.assert_called_once_with(registration.action.pk)


@pytest.mark.django_db
def test_invalid_subscriber_key(
    mock_check_unfinished, mock_finish, submission_task_patch
):
    client = APIClient()

    first_subscriber = Client.objects.first()
    second_subscriber = baker.make_recipe("multi_tenant.client")
    baker.make_recipe("multi_tenant.subscriberslug", subscriber=second_subscriber)
    assert Client.objects.count() == 4

    url = f"{REGISTER_API_ENDPOINT}?subscriber=INVALID"
    response = client.post(url, VALID_REGISTRATION)
    assert response.status_code == 200
    assert "uuid" in response.json()

    registration = Registration.objects.first()
    assert response.json()["uuid"] == str(registration.uuid)
    assert registration.subscriber == first_subscriber

    submission_task_patch.assert_called_once_with(registration, "FOUNDER123", True)
    mock_finish.delay.assert_called_once_with(registration.action.pk)


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
def test_event_tracking(mock_upsell, mock_check_unfinished):
    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE,
        {**VALID_REGISTRATION, "initial_events": [EventType.FINISH_EXTERNAL.value]},
    )
    assert register_response.status_code == 200

    registration = Registration.objects.first()

    assert Event.objects.count() == 2

    assert (
        Event.objects.filter(
            action=registration.action, event_type=EventType.START
        ).count()
        == 1
    )

    assert (
        Event.objects.filter(
            action=registration.action, event_type=EventType.FINISH_EXTERNAL
        ).count()
        == 1
    )

    mock_upsell.assert_called_once()


@pytest.mark.django_db
def test_update_status(mock_check_unfinished):
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
def test_invalid_update_status(mock_check_unfinished):
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
def test_bad_update_status(mock_check_unfinished):
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


@pytest.fixture
def mock_region(mocker):
    class FakeRegion(object):
        def __init__(self, name, external_id):
            self.name = name
            self.external_id = external_id

    mocker.patch(
        "register.pa.geocode_to_regions",
        return_value=[FakeRegion(name="Clarion County", external_id=432147)],
    )
    mocker.patch(
        "register.pa.Region.objects.get",
        return_value=FakeRegion(name="Clarion County", external_id=432147),
    )


@pytest.fixture
def mock_few_regions(mocker):
    class FakeRegion(object):
        def __init__(self, name, external_id):
            self.name = name
            self.external_id = external_id

    mocker.patch(
        "register.pa.geocode_to_regions",
        return_value=[
            FakeRegion(name="Clarion County", external_id=432147),
            FakeRegion(name="Foo County", external_id=123456),
            FakeRegion(name="Bar County", external_id=789012),
        ],
    )
    mocker.patch(
        "register.pa.Region.objects.get",
        return_value=FakeRegion(name="Clarion County", external_id=432147),
    )


@pytest.fixture
def mock_all_regions(mocker):
    class FakeRegion(object):
        def __init__(self, name, external_id):
            self.name = name
            self.external_id = external_id

    mocker.patch(
        "register.pa.geocode_to_regions", return_value=[],
    )
    mocker.patch(
        "register.pa.Region.objects.get",
        return_value=FakeRegion(name="Clarion County", external_id=432147),
    )
    m = mocker.patch("register.pa.Region.visible.filter",)
    m.return_value.order_by.return_value = [
        FakeRegion(name="Clarion County", external_id=432147),
        FakeRegion(name="A County", external_id=432141),
        FakeRegion(name="B County", external_id=432142),
        FakeRegion(name="C County", external_id=432143),
        FakeRegion(name="D County", external_id=432144),
        FakeRegion(name="E County", external_id=432145),
    ]


@pytest.fixture
def mock_ovrlib_session_dl(mocker):
    class FakeSession(object):
        def __init__(self, api_key, staging):
            pass

        def register(self, registration):
            return ovrlib.PAOVRResponse(
                application_id="123",
                application_date=datetime.date(year=2020, month=6, day=1),
                signature_source="DL",
            )

    return mocker.patch("ovrlib.pa.PAOVRSession", FakeSession)


@pytest.mark.django_db
def test_pa_nodlorsig(
    mock_check_unfinished, mock_ovrlib_session_dl, mock_region, state_confirmation_email
):
    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE, PA_REGISTRATION_START, format="json",
    )
    assert register_response.status_code == 200
    assert "uuid" in register_response.json()
    assert register_response.json().get("state_api_regions") == [
        {"external_id": 432147, "name": "Clarion County",}
    ]

    registration = Registration.objects.first()
    assert register_response.json()["uuid"] == str(registration.uuid)
    assert registration.status == TurnoutActionStatus.INCOMPLETE

    register_response = client.patch(
        PATCH_API_ENDPOINT.format(uuid=registration.uuid),
        PA_REGISTRATION_NODLSSNORSIG,
        format="json",
    )
    assert register_response.status_code == 200
    assert register_response.json()["state_api_status"] == "failure"
    assert register_response.json()["state_api_error"] == "no_dl_or_signature"
    assert not state_confirmation_email.called


@pytest.mark.django_db
def test_pa_nodlorsig_few_regions(
    mock_check_unfinished,
    mock_ovrlib_session_dl,
    mock_few_regions,
    state_confirmation_email,
):
    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE, PA_REGISTRATION_START, format="json",
    )
    assert register_response.status_code == 200
    assert "uuid" in register_response.json()
    assert register_response.json().get("state_api_regions") == [
        {"external_id": 432147, "name": "Clarion County",},
        {"external_id": 123456, "name": "Foo County",},
        {"external_id": 789012, "name": "Bar County",},
    ]

    registration = Registration.objects.first()
    assert register_response.json()["uuid"] == str(registration.uuid)
    assert registration.status == TurnoutActionStatus.INCOMPLETE

    register_response = client.patch(
        PATCH_API_ENDPOINT.format(uuid=registration.uuid),
        PA_REGISTRATION_NODLSSNORSIG,
        format="json",
    )
    assert register_response.status_code == 200
    assert register_response.json()["state_api_status"] == "failure"
    assert register_response.json()["state_api_error"] == "no_dl_or_signature"
    assert not state_confirmation_email.called


@pytest.mark.django_db
def test_pa_nodlorsig_all_regions(
    mock_check_unfinished,
    mock_ovrlib_session_dl,
    mock_all_regions,
    state_confirmation_email,
):
    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE, PA_REGISTRATION_START, format="json",
    )
    assert register_response.status_code == 200
    assert "uuid" in register_response.json()
    assert len(register_response.json().get("state_api_regions")) == 6

    registration = Registration.objects.first()
    assert register_response.json()["uuid"] == str(registration.uuid)
    assert registration.status == TurnoutActionStatus.INCOMPLETE

    register_response = client.patch(
        PATCH_API_ENDPOINT.format(uuid=registration.uuid),
        PA_REGISTRATION_NODLSSNORSIG,
        format="json",
    )
    assert register_response.status_code == 200
    assert register_response.json()["state_api_status"] == "failure"
    assert register_response.json()["state_api_error"] == "no_dl_or_signature"
    assert not state_confirmation_email.called


@pytest.mark.django_db
def test_pa_dl(
    mock_check_unfinished,
    mock_finish,
    submission_task_patch,
    mock_ovrlib_session_dl,
    mock_region,
    state_confirmation_email,
):
    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE, PA_REGISTRATION_START, format="json",
    )
    assert register_response.status_code == 200
    assert "uuid" in register_response.json()
    assert register_response.json().get("state_api_regions") == [
        {"external_id": 432147, "name": "Clarion County",}
    ]

    registration = Registration.objects.first()
    assert register_response.json()["uuid"] == str(registration.uuid)
    assert registration.status == TurnoutActionStatus.INCOMPLETE

    register_response = client.patch(
        PATCH_API_ENDPOINT.format(uuid=registration.uuid),
        PA_REGISTRATION_DL,
        format="json",
    )
    assert register_response.status_code == 200
    assert register_response.json()["state_api_status"] == "success"

    registration = Registration.objects.first()
    assert registration.party == PoliticalParties.OTHER
    assert registration.state_fields["party_other"] == "Foo"

    state_confirmation_email.assert_called_once_with(registration.pk)
    mock_finish.delay.assert_called_once_with(registration.action.pk)


@pytest.fixture
def mock_ovrlib_session_baddl(mocker):
    class FakeSession(object):
        def __init__(self, api_key, staging):
            pass

        def register(self, request):
            if request.dl_number:
                raise ovrlib.exceptions.InvalidDLError
            return ovrlib.PAOVRResponse(
                application_id="123",
                application_date=datetime.date(year=2020, month=6, day=1),
                signature_source="signature",
            )

    return mocker.patch("ovrlib.pa.PAOVRSession", FakeSession)


@pytest.fixture
def mock_ovrlib_session_badssn(mocker):
    class FakeSession(object):
        def __init__(self, api_key, staging):
            pass

        def register(self, request):
            if request.dl_number:
                raise ovrlib.exceptions.InvalidDLError
            return ovrlib.PAOVRResponse(
                application_id="123",
                application_date=datetime.date(year=2020, month=6, day=1),
                signature_source="signature",
            )

    return mocker.patch("ovrlib.pa.PAOVRSession", FakeSession)


@pytest.mark.django_db
def test_pa_sig(
    mock_check_unfinished,
    mock_finish,
    submission_task_patch,
    mock_ovrlib_session_baddl,
    mock_region,
    state_confirmation_email,
):
    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE, PA_REGISTRATION_START, format="json",
    )
    assert register_response.status_code == 200
    assert "uuid" in register_response.json()
    assert register_response.json().get("state_api_regions") == [
        {"external_id": 432147, "name": "Clarion County",}
    ]

    registration = Registration.objects.first()
    assert register_response.json()["uuid"] == str(registration.uuid)
    assert registration.status == TurnoutActionStatus.INCOMPLETE

    register_response = client.patch(
        PATCH_API_ENDPOINT.format(uuid=registration.uuid),
        PA_REGISTRATION_BADDL,
        format="json",
    )
    assert register_response.status_code == 200
    assert register_response.json()["state_api_status"] == "failure"
    assert register_response.json()["state_api_error"] == "dl_invalid"
    assert not state_confirmation_email.called

    # image
    item = SecureUploadItem.objects.create(
        upload_type=SecureUploadType.SIGNATURE, content_type="image/jpeg",
    )
    item.file.save(
        str(SmallUUID()), ContentFile("foo"), True,
    )
    item.save()
    PA_REGISTRATION_SIG["state_fields"]["signature"] = item.uuid

    register_response = client.patch(
        PATCH_API_ENDPOINT.format(uuid=registration.uuid),
        PA_REGISTRATION_SIG,
        format="json",
    )
    assert register_response.status_code == 200
    assert register_response.json()["state_api_status"] == "success"

    registration = Registration.objects.first()
    assert registration.party == PoliticalParties.NONE

    state_confirmation_email.assert_called_once_with(registration.uuid)
    mock_finish.delay.assert_called_once_with(registration.action.pk)


@pytest.mark.django_db
def test_complete_lob(
    submission_task_patch, mock_check_unfinished, mock_finish, mock_verify_address,
):
    # enable print-and-forward for this state
    set_state_allow_print_and_forward(VALID_REGISTRATION["state"])

    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE, VALID_REGISTRATION
    )
    assert register_response.status_code == 200
    assert "uuid" in register_response.json()

    registration = Registration.objects.first()
    assert register_response.json()["uuid"] == str(registration.uuid)
    assert register_response.json()["allow_print_and_forward"] == True
    assert registration.status == TurnoutActionStatus.INCOMPLETE
    assert (
        Event.objects.filter(
            action=registration.action, event_type=EventType.START
        ).count()
        == 1
    )

    # complete with request_mailing address
    status_response = client.patch(
        PATCH_API_ENDPOINT.format(uuid=registration.uuid), VALID_PATCH_MAIL
    )
    assert status_response.status_code == 200

    # refresh from database, make sure it's the same object
    registration.refresh_from_db()
    assert str(registration.uuid) == register_response.json()["uuid"]
    mock_finish.delay.assert_called_once_with(registration.action.pk)


@pytest.mark.django_db
def test_complete_lob_ignore_undeliverable(
    submission_task_patch, mock_check_unfinished, mock_finish, mock_verify_address,
):
    # enable print-and-forward for this state
    set_state_allow_print_and_forward(VALID_REGISTRATION["state"])

    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE, VALID_REGISTRATION
    )
    assert register_response.status_code == 200
    assert "uuid" in register_response.json()

    registration = Registration.objects.first()
    assert register_response.json()["uuid"] == str(registration.uuid)
    assert register_response.json()["allow_print_and_forward"] == True
    assert register_response.json()["request_mailing_deliverable"] == None
    assert registration.status == TurnoutActionStatus.INCOMPLETE
    assert (
        Event.objects.filter(
            action=registration.action, event_type=EventType.START
        ).count()
        == 1
    )

    # (fail) complete with request_mailing address (undeliverable)
    mock_verify_address.return_value = (False, {})

    status_response = client.patch(
        PATCH_API_ENDPOINT.format(uuid=registration.uuid), VALID_PATCH_MAIL
    )
    assert status_response.status_code == 400
    assert "request_mailing_address1" in status_response.json()
    assert status_response.json()["request_mailing_deliverable_not_ignored"]

    registration.refresh_from_db()
    assert str(registration.uuid) == register_response.json()["uuid"]
    assert registration.status == TurnoutActionStatus.INCOMPLETE

    # try again, and ignore
    info = VALID_PATCH_MAIL.copy()
    info["ignore_undeliverable"] = True

    status_response = client.patch(
        PATCH_API_ENDPOINT.format(uuid=registration.uuid), info
    )
    assert status_response.status_code == 200

    registration.refresh_from_db()
    assert str(registration.uuid) == register_response.json()["uuid"]
    assert registration.status != TurnoutActionStatus.INCOMPLETE
    mock_finish.delay.assert_called_once_with(registration.action.pk)


@pytest.mark.django_db
def test_complete_lob_disallow(
    submission_task_patch, mock_check_unfinished, mock_verify_address,
):
    client = APIClient()
    register_response = client.post(
        REGISTER_API_ENDPOINT_INCOMPLETE, VALID_REGISTRATION
    )
    assert register_response.status_code == 200
    assert "uuid" in register_response.json()

    registration = Registration.objects.first()
    assert register_response.json()["uuid"] == str(registration.uuid)
    assert register_response.json()["allow_print_and_forward"] == False
    assert register_response.json()["request_mailing_deliverable"] == None
    assert registration.status == TurnoutActionStatus.INCOMPLETE
    assert (
        Event.objects.filter(
            action=registration.action, event_type=EventType.START
        ).count()
        == 1
    )

    # try to complete with request_mailing address
    status_response = client.patch(
        PATCH_API_ENDPOINT.format(uuid=registration.uuid), VALID_PATCH_MAIL
    )
    assert status_response.status_code == 400
    registration.refresh_from_db()
    assert str(registration.uuid) == register_response.json()["uuid"]
    assert registration.request_mailing_address1 is None
    assert registration.request_mailing_city is None
    assert registration.request_mailing_state is None
    assert registration.request_mailing_zipcode is None


@pytest.mark.django_db
def test_complete_lob_disallow2(
    submission_task_patch, mock_check_unfinished, mock_verify_address,
):
    client = APIClient()
    ref = VALID_REGISTRATION.copy()
    ref["request_mailing_address1"] = "123 A St."
    register_response = client.post(REGISTER_API_ENDPOINT_INCOMPLETE, ref)
    assert register_response.status_code == 400

    ref["request_mailing_address1"] = ""
    ref["request_mailing_city"] = ""
    register_response = client.post(REGISTER_API_ENDPOINT_INCOMPLETE, ref)
    assert register_response.status_code == 200


# Test confirmation link that sends the actual letter
@pytest.mark.django_db
def test_lob_confirm(mocker):
    registration = baker.make_recipe(
        "register.registration",
        result_item_mail=baker.make_recipe("storage.registration_form"),
    )

    # send_date = datetime.datetime(2020, 1, 1, 1, 1, 1)
    # send = mocker.patch("register.api_views.send_letter", return_value=send_date)

    client = APIClient()
    response = client.put(
        LOB_LETTER_CONFIRM_API_ENDPOINT.format(
            uuid=registration.action.uuid, token=generate_lob_token(registration)
        ),
    )

    assert response.status_code == 503
    assert "error" in response.json()
    # assert response.json() == {"send_date": send_date.isoformat()}
    # send.assert_called_once_with(registration)


@pytest.mark.django_db
def test_lob_confirm_dne(mocker):
    client = APIClient()

    response = client.put(
        LOB_LETTER_CONFIRM_API_ENDPOINT.format(
            uuid="7e6abe5f-7cc7-4d9a-96f1-75c9e6c05ed8", token="bar",
        )
    )
    assert response.status_code == 404
