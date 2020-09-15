import datetime

import pytest
from django.conf import settings
from model_bakery import baker
from rest_framework.test import APIClient

from absentee.contactinfo import AbsenteeContactInfo
from absentee.models import BallotRequest, LeoContactOverride, RegionEsignMethod
from common.enums import (
    EventType,
    StateFieldFormats,
    SubmissionType,
    TurnoutActionStatus,
)
from election.models import StateInformation, StateInformationFieldType
from event_tracking.models import Event
from integration.lob import generate_lob_token
from official.models import Address, Office

ABSENTEE_API_ENDPOINT_INCOMPLETE = (
    "/v1/absentee/request/?incomplete=true&match_region=true"
)
ABSENTEE_API_ENDPOINT_INCOMPLETE_NO_REGION_MATCH = (
    "/v1/absentee/request/?incomplete=true"
)
ABSENTEE_API_ENDPOINT_COMPLETE = "/v1/absentee/request/"

ABSENTEE_API_ENDPOINT_PATCH_INCOMPLETE = "/v1/absentee/request/{uuid}/?incomplete=true"

ABSENTEE_API_ENDPOINT_PATCH_COMPLETE = "/v1/absentee/request/{uuid}/"

LOB_LETTER_CONFIRM_API_ENDPOINT = (
    "/v1/absentee/confirm-print-and-forward/{uuid}/?token={token}"
)

VALID_ABSENTEE_INITIAL = {
    "title": "Mr",
    "first_name": "John",
    "last_name": "Hancock",
    "address1": "30 Beacon Street",
    "city": "Boston",
    "state": "MA",
    "email": "john@hancock.local",
    "date_of_birth": "1737-01-23",
    "zipcode": "02108",
    "phone": "+16175557890",
    "sms_opt_in_subscriber": True,
}

VALID_ABSENTEE_FULL = {
    "title": "Mr",
    "first_name": "John",
    "last_name": "Hancock",
    "address1": "30 Beacon Street",
    "city": "Boston",
    "state": "MA",
    "email": "john@hancock.local",
    "date_of_birth": "1737-01-23",
    "zipcode": "02108",
    "phone": "+16175557890",
    "sms_opt_in_subscriber": True,
    "region": 12345,
    "us_citizen": True,
    "is_18_or_over": True,
}

VALID_ABSENTEE_FULL_MAIL = {
    "title": "Mr",
    "first_name": "John",
    "last_name": "Hancock",
    "address1": "30 Beacon Street",
    "city": "Boston",
    "state": "MA",
    "email": "john@hancock.local",
    "date_of_birth": "1737-01-23",
    "zipcode": "02108",
    "phone": "+16175557890",
    "sms_opt_in": True,
    "sms_opt_in_subscriber": True,
    "region": 12345,
    "us_citizen": True,
    "is_18_or_over": True,
}

INVALID_STATE_FIELDS = {
    "title": "Mr",
    "first_name": "John",
    "last_name": "Hancock",
    "address1": "30 Beacon Street",
    "city": "Boston",
    "state": "MA",
    "email": "john@hancock.local",
    "date_of_birth": "1737-01-23",
    "zipcode": "02108",
    "phone": "+16175557890",
    "sms_opt_in_subscriber": True,
    "state_fields": "this should be a dict, not a string",
}


@pytest.fixture
def mock_check_unfinished(mocker):
    settings.SMS_POST_SIGNUP_ALERT = False
    return mocker.patch("absentee.api_views.action_check_unfinished")


@pytest.fixture
def mock_finish(mocker):
    return mocker.patch("absentee.api_views.action_finish")


@pytest.fixture
def mock_get_absentee_contact_info(mocker):
    return mocker.patch("absentee.api_views.get_absentee_contact_info")


@pytest.fixture
def mock_get_regions_for_address(mocker):
    return mocker.patch("absentee.api_views.get_regions_for_address")


@pytest.fixture
def mock_verify_address(mocker):
    return mocker.patch("integration.lob.verify_address", return_value=(True, {}))


@pytest.fixture
def process_ballot_request(mocker):
    return mocker.patch("absentee.api_views.process_ballot_request")


@pytest.fixture(autouse=True)
def mock_ovbm_link(mocker):
    mock = mocker.patch("absentee.api_views.ovbm_link_for_ballot_request")
    mock.return_value = "mock-ovbm-link"

    return mock


def set_feature_flag(mocker, val):
    mocker.patch("absentee.api_views.flag_enabled_for_state").return_value = val


@pytest.fixture
def feature_flag_off(mocker):
    set_feature_flag(mocker, False)


@pytest.fixture
def feature_flag_on(mocker):
    set_feature_flag(mocker, True)


def set_state_bool_info(state, name, value):
    ft = StateInformationFieldType(slug=name, field_format=StateFieldFormats.BOOLEAN)
    ft.save()

    info = StateInformation.objects.get(state=state, field_type=ft)
    info.text = "true" if value else "false"
    info.save()


def set_email_allowed(state):
    set_state_bool_info(state, "vbm_app_submission_email", True)


def set_email_forbidden(state):
    set_state_bool_info(state, "vbm_app_submission_email", False)


def set_fax_allowed(state):
    set_state_bool_info(state, "vbm_app_submission_fax", True)


def set_fax_forbidden(state):
    set_state_bool_info(state, "vbm_app_submission_fax", False)


@pytest.mark.django_db
def test_bad_state_fields():
    state = baker.make_recipe("election.state", code=INVALID_STATE_FIELDS["state"],)
    client = APIClient()
    response = client.post(ABSENTEE_API_ENDPOINT_INCOMPLETE, INVALID_STATE_FIELDS)
    assert response.status_code == 400
    assert "state_fields" in response.json()


# Incomplete create, matching region
@pytest.mark.django_db
def test_incomplete_create_single_matching_region(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_get_regions_for_address,
    mock_verify_address,
    feature_flag_off,
):
    state = baker.make_recipe("election.state", code=VALID_ABSENTEE_INITIAL["state"],)

    mock_get_regions_for_address.return_value = (
        [baker.make_recipe("official.region", external_id=12345)],
        False,
    )

    client = APIClient()
    response = client.post(ABSENTEE_API_ENDPOINT_INCOMPLETE, VALID_ABSENTEE_INITIAL)

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "region": 12345,
        "esign_method": "self_print",
        "ovbm_link": "mock-ovbm-link",
        "allow_print_and_forward": False,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }

    mock_get_regions_for_address.assert_called_with(
        street=VALID_ABSENTEE_INITIAL["address1"],
        city=VALID_ABSENTEE_INITIAL["city"],
        state=VALID_ABSENTEE_INITIAL["state"],
        zipcode=VALID_ABSENTEE_INITIAL["zipcode"],
    )


# Incomplete create, matching region, email
@pytest.mark.django_db
def test_incomplete_create_single_matching_region_email(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_get_regions_for_address,
    mock_verify_address,
    feature_flag_on,
):
    state = baker.make_recipe("election.state", code=VALID_ABSENTEE_INITIAL["state"])
    set_email_allowed(state)

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(
        email="foo@example.com"
    )
    mock_get_regions_for_address.return_value = (
        [baker.make_recipe("official.region", external_id=12345)],
        False,
    )

    client = APIClient()
    response = client.post(ABSENTEE_API_ENDPOINT_INCOMPLETE, VALID_ABSENTEE_INITIAL)

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "region": 12345,
        "esign_method": "leo_email",
        "ovbm_link": "mock-ovbm-link",
        "allow_print_and_forward": False,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }


# Incomplete create, region matching error
@pytest.mark.django_db
def test_incomplete_create_region_matching_error(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_get_regions_for_address,
    mock_verify_address,
):
    state = baker.make_recipe("election.state", code=VALID_ABSENTEE_INITIAL["state"],)

    baker.make_recipe("official.region", state=state, name="B", external_id=2)
    baker.make_recipe("official.region", state=state, name="C", external_id=3)
    baker.make_recipe("official.region", state=state, name="A", external_id=1)

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(
        fax="+16175551234"
    )
    mock_get_regions_for_address.return_value = (None, True)

    client = APIClient()
    response = client.post(ABSENTEE_API_ENDPOINT_INCOMPLETE, VALID_ABSENTEE_INITIAL)

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "region": None,
        "esign_method": None,
        "ovbm_link": "mock-ovbm-link",
        "regions": [
            {"name": "A", "external_id": 1},
            {"name": "B", "external_id": 2},
            {"name": "C", "external_id": 3},
        ],
        "allow_print_and_forward": False,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }


# Incomplete create, no matching regions
@pytest.mark.django_db
def test_incomplete_create_no_matching_regions(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_get_regions_for_address,
    mock_verify_address,
):
    state = baker.make_recipe("election.state", code=VALID_ABSENTEE_INITIAL["state"],)

    baker.make_recipe("official.region", state=state, name="B", external_id=2)
    baker.make_recipe("official.region", state=state, name="C", external_id=3)
    baker.make_recipe("official.region", state=state, name="A", external_id=1)

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(
        fax="+16175551234"
    )
    mock_get_regions_for_address.return_value = ([], False)

    client = APIClient()
    response = client.post(ABSENTEE_API_ENDPOINT_INCOMPLETE, VALID_ABSENTEE_INITIAL)

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "region": None,
        "esign_method": None,
        "ovbm_link": "mock-ovbm-link",
        "regions": [
            {"name": "A", "external_id": 1},
            {"name": "B", "external_id": 2},
            {"name": "C", "external_id": 3},
        ],
        "allow_print_and_forward": False,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }


# Incomplete create, multiple matching regions
@pytest.mark.django_db
def test_incomplete_create_multiple_matching_regions(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_get_regions_for_address,
    mock_verify_address,
):
    state = baker.make_recipe("election.state", code=VALID_ABSENTEE_INITIAL["state"],)

    r1 = baker.make_recipe("official.region", state=state, name="B", external_id=2)
    r2 = baker.make_recipe("official.region", state=state, name="C", external_id=3)
    baker.make_recipe("official.region", state=state, name="A", external_id=1)

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(
        fax="+16175551234"
    )
    mock_get_regions_for_address.return_value = ([r1, r2], False)

    client = APIClient()
    response = client.post(ABSENTEE_API_ENDPOINT_INCOMPLETE, VALID_ABSENTEE_INITIAL)

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "region": None,
        "esign_method": None,
        "ovbm_link": "mock-ovbm-link",
        "regions": [{"name": "B", "external_id": 2}, {"name": "C", "external_id": 3},],
        "allow_print_and_forward": False,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }


# Incomplete create, no region matching requested
@pytest.mark.django_db
def test_incomplete_create_no_region_matching(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_get_regions_for_address,
    mock_verify_address,
):
    state = baker.make_recipe("election.state", code=VALID_ABSENTEE_INITIAL["state"],)

    r1 = baker.make_recipe("official.region", state=state, name="B", external_id=2)
    baker.make_recipe("official.region", state=state, name="C", external_id=3)
    baker.make_recipe("official.region", state=state, name="A", external_id=1)

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(
        fax="+16175551234"
    )
    mock_get_regions_for_address.return_value = ([r1], False)

    client = APIClient()
    response = client.post(
        ABSENTEE_API_ENDPOINT_INCOMPLETE_NO_REGION_MATCH, VALID_ABSENTEE_INITIAL
    )

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "region": None,
        "esign_method": None,
        "ovbm_link": "mock-ovbm-link",
        "regions": [
            {"name": "A", "external_id": 1},
            {"name": "B", "external_id": 2},
            {"name": "C", "external_id": 3},
        ],
        "allow_print_and_forward": False,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }


# Complete create
@pytest.mark.django_db
def test_complete_create(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_get_regions_for_address,
    mock_verify_address,
    mock_finish,
    process_ballot_request,
    feature_flag_on,
):
    state = baker.make_recipe("election.state", code=VALID_ABSENTEE_INITIAL["state"],)
    set_fax_allowed(state)

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(
        fax="+16175551234"
    )
    mock_get_regions_for_address.return_value = (
        [baker.make_recipe("official.region", external_id=12345)],
        False,
    )

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(
        fax="+16175551234"
    )

    client = APIClient()
    response = client.post(ABSENTEE_API_ENDPOINT_COMPLETE, VALID_ABSENTEE_FULL)

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "esign_method": "leo_fax",
        "ovbm_link": "mock-ovbm-link",
        "region": 12345,
        "allow_print_and_forward": False,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }

    assert ballot_request.region.external_id == 12345

    mock_finish.delay.assert_called_once_with(ballot_request.action.pk)
    process_ballot_request.assert_called_with(ballot_request, None, True)


# Incomplete update, not filling in esign method
@pytest.mark.django_db
def test_incomplete_update_no_esign_filling(mock_check_unfinished, mock_verify_address):
    state = baker.make_recipe("election.state", code=VALID_ABSENTEE_INITIAL["state"],)

    client = APIClient()
    client.post(
        ABSENTEE_API_ENDPOINT_INCOMPLETE_NO_REGION_MATCH, VALID_ABSENTEE_INITIAL
    )

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    response = client.patch(
        ABSENTEE_API_ENDPOINT_PATCH_INCOMPLETE.format(uuid=ballot_request.uuid),
        {"address1": "new_address",},
    )

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "esign_method": None,
        "ovbm_link": "mock-ovbm-link",
        "region": None,
        "allow_print_and_forward": False,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }

    assert BallotRequest.objects.count() == 1
    ballot_request_new = BallotRequest.objects.first()

    assert ballot_request_new.address1 == "new_address"


# Incomplete update, filling in esign method
@pytest.mark.django_db
def test_incomplete_update_with_esign_filling(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_verify_address,
    feature_flag_on,
):
    state = baker.make_recipe("election.state", code=VALID_ABSENTEE_INITIAL["state"])
    set_fax_allowed(state)
    baker.make_recipe("official.region", external_id=12345)

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(
        fax="+16175551234"
    )

    client = APIClient()
    client.post(
        ABSENTEE_API_ENDPOINT_INCOMPLETE_NO_REGION_MATCH, VALID_ABSENTEE_INITIAL
    )

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    response = client.patch(
        ABSENTEE_API_ENDPOINT_PATCH_INCOMPLETE.format(uuid=ballot_request.uuid),
        {"address1": "new_address", "region": 12345},
    )

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "esign_method": "leo_fax",
        "ovbm_link": "mock-ovbm-link",
        "region": 12345,
        "allow_print_and_forward": False,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }


# Complete update
@pytest.mark.django_db
def test_complete_update(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_verify_address,
    mock_finish,
    process_ballot_request,
    feature_flag_on,
):
    state = baker.make_recipe("election.state", code=VALID_ABSENTEE_INITIAL["state"])
    set_fax_allowed(state)
    baker.make_recipe("official.region", external_id=12345)

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(
        fax="+16175551234"
    )

    client = APIClient()
    client.post(
        ABSENTEE_API_ENDPOINT_INCOMPLETE_NO_REGION_MATCH, VALID_ABSENTEE_INITIAL
    )

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    response = client.patch(
        ABSENTEE_API_ENDPOINT_PATCH_COMPLETE.format(uuid=ballot_request.uuid),
        {
            "address1": "new_address",
            "region": 12345,
            "us_citizen": True,
            "is_18_or_over": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "esign_method": "leo_fax",
        "ovbm_link": "mock-ovbm-link",
        "region": 12345,
        "allow_print_and_forward": False,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }

    mock_finish.delay.assert_called_once_with(ballot_request.action.pk)
    process_ballot_request.assert_called_with(ballot_request, None, True)


@pytest.mark.parametrize(
    "flag,email_allowed,fax_allowed,email_contact,fax_contact,submission_override,expected",
    [
        # Flag on, email and fax allowed, both contact infos -> email
        (True, True, True, True, True, None, SubmissionType.LEO_EMAIL),
        # Flag off, email and fax allowed, both contact info -> self-print
        (False, True, True, True, True, None, SubmissionType.SELF_PRINT),
        # Flag on, email and fax allowed, only fax number -> fax
        (True, True, True, False, True, None, SubmissionType.LEO_FAX),
        # Flag on, email and fax allowed, no contact -> self-print
        (True, True, True, False, False, None, SubmissionType.SELF_PRINT),
        # Flag on, email allowed, fax number -> self-print
        (True, True, None, False, True, None, SubmissionType.SELF_PRINT),
        # Flag on, fax allowed, email and fax number -> fax
        (True, None, True, True, True, None, SubmissionType.LEO_FAX),
        # Flag on, email allowed, email -> email
        (True, True, None, True, False, None, SubmissionType.LEO_EMAIL),
        # Flag on, nothing allowed, both contact infos -> self-print
        (True, None, None, True, True, None, SubmissionType.SELF_PRINT),
        # Flag on, email and fax explicitly disallowed, both contact infos -> self-print
        (True, False, False, True, True, None, SubmissionType.SELF_PRINT),
        # Flag on, email disallowed, fax allowed, both contact infos -> fax
        (True, False, True, True, True, None, SubmissionType.LEO_FAX),
        # Flag on, email and fax allowed, both contact infos, fax override -> fax
        (True, True, True, True, True, SubmissionType.LEO_FAX, SubmissionType.LEO_FAX),
        # Flag on, email allowed, both contact infos, fax override -> self-print
        (
            True,
            True,
            False,
            True,
            True,
            SubmissionType.LEO_FAX,
            SubmissionType.SELF_PRINT,
        ),
        # Flag on, both allowed, only email, fax override -> self-print
        (
            True,
            True,
            True,
            True,
            False,
            SubmissionType.LEO_FAX,
            SubmissionType.SELF_PRINT,
        ),
        # Flag on, email allowed, only email, email override -> email
        (
            True,
            True,
            False,
            True,
            False,
            SubmissionType.LEO_EMAIL,
            SubmissionType.LEO_EMAIL,
        ),
        # Flag on, email and fax allowed, both contact infos, self-print override -> self-print
        (
            True,
            True,
            True,
            True,
            True,
            SubmissionType.SELF_PRINT,
            SubmissionType.SELF_PRINT,
        ),
    ],
)
@pytest.mark.django_db
def test_get_esign_method(
    flag,
    email_allowed,
    fax_allowed,
    email_contact,
    fax_contact,
    submission_override,
    expected,
    mocker,
    mock_check_unfinished,
    mock_get_regions_for_address,
    mock_verify_address,
):
    set_feature_flag(mocker, flag)

    state = baker.make_recipe("election.state", code=VALID_ABSENTEE_INITIAL["state"])

    # email_allowed/fax_allowed are ternary: they can be allowed, disallowed,
    # or None (indicating we don't have data for that state)
    if email_allowed == True:
        set_email_allowed(state)
    elif email_allowed == False:
        set_email_forbidden(state)

    if fax_allowed == True:
        set_fax_allowed(state)
    elif fax_allowed == False:
        set_fax_forbidden(state)

    # Set mock contact info
    mock_get_regions_for_address.return_value = (
        [baker.make_recipe("official.region", external_id=12345, state_id="MA")],
        False,
    )

    if submission_override:
        # set up the submission_override
        props = {
            "region_id": 12345,
            "submission_method": submission_override,
        }

        if email_contact:
            props["email"] = "foo@example.com"

        if fax_contact:
            props["fax"] = "+16175551234"

        LeoContactOverride(**props).save()
    else:
        # set up USVF contact info
        office = Office(region_id=12345, external_id=67890)
        office.save()

        address = Address(office=office, external_id=11111)

        if email_contact:
            address.email = "foo@example.com"

        if fax_contact:
            address.fax = "+16175551234"

        address.save()

    # Run the test!
    client = APIClient()
    client.post(ABSENTEE_API_ENDPOINT_INCOMPLETE, VALID_ABSENTEE_INITIAL)

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    assert ballot_request.esign_method == expected

    # Also check the view -- ensure the view logic matches the python logic
    if flag:
        esign_method_record = RegionEsignMethod.objects.get(region_id=12345)
        assert esign_method_record.submission_method == expected


# Complete lob
@pytest.mark.django_db
def test_complete_lob(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_verify_address,
    mock_finish,
    process_ballot_request,
    feature_flag_on,
):
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        allow_absentee_print_and_forward=True,
    )
    baker.make_recipe("official.region", external_id=12345)

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(
        fax="+16175551234"
    )

    client = APIClient()
    response = client.post(
        ABSENTEE_API_ENDPOINT_INCOMPLETE_NO_REGION_MATCH, VALID_ABSENTEE_INITIAL
    )

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "esign_method": None,
        "ovbm_link": "mock-ovbm-link",
        "region": None,
        "regions": [],
        "allow_print_and_forward": True,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }

    # bad address
    mock_verify_address.return_value = (False, {})
    response = client.patch(
        ABSENTEE_API_ENDPOINT_PATCH_INCOMPLETE.format(uuid=ballot_request.uuid),
        {
            "request_mailing_address1": "123 A St NW foo",
            "request_mailing_city": "Washington",
            "request_mailing_state": "DC",
            "request_mailing_zipcode": "20001",
            "region": 12345,
        },
    )

    assert response.status_code == 400
    assert "request_mailing_address1" in response.json()
    assert response.json()["request_mailing_deliverable_not_ignored"]

    # try to complete (and fail!) with undeliverable request_mailing_address
    response = client.patch(
        ABSENTEE_API_ENDPOINT_PATCH_COMPLETE.format(uuid=ballot_request.uuid),
        {
            "address1": "new_address",
            "region": 12345,
            "us_citizen": True,
            "is_18_or_over": True,
        },
    )

    assert response.status_code == 400
    assert "request_mailing_address1" in response.json()
    assert response.json()["request_mailing_deliverable_not_ignored"]
    process_ballot_request.assert_not_called()
    ballot_request = BallotRequest.objects.first()
    assert ballot_request.status != TurnoutActionStatus.PENDING

    # now fields change, address is now good
    mock_verify_address.return_value = (True, {})
    response = client.patch(
        ABSENTEE_API_ENDPOINT_PATCH_INCOMPLETE.format(uuid=ballot_request.uuid),
        {
            "address1": VALID_ABSENTEE_INITIAL["address1"],
            "request_mailing_address1": "123 A St NW",
            "request_mailing_city": "Washington",
            "request_mailing_state": "DC",
            "request_mailing_zipcode": "20001",
            "region": 12345,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "esign_method": "self_print",
        "ovbm_link": "mock-ovbm-link",
        "region": 12345,
        "allow_print_and_forward": True,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": True,
    }

    # Complete!
    response = client.patch(
        ABSENTEE_API_ENDPOINT_PATCH_COMPLETE.format(uuid=ballot_request.uuid),
        {
            "address1": "new_address",
            "region": 12345,
            "us_citizen": True,
            "is_18_or_over": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "esign_method": "self_print",
        "ovbm_link": "mock-ovbm-link",
        "region": 12345,
        "allow_print_and_forward": True,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": True,
    }

    mock_finish.delay.assert_called_once_with(ballot_request.action.pk)
    process_ballot_request.assert_called_with(ballot_request, None, True)


# Complete lob
@pytest.mark.django_db
def test_complete_lob_force_undeliverable(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_verify_address,
    mock_finish,
    process_ballot_request,
    feature_flag_on,
):
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        allow_absentee_print_and_forward=True,
    )
    baker.make_recipe("official.region", external_id=12345)

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(
        fax="+16175551234"
    )

    client = APIClient()
    response = client.post(
        ABSENTEE_API_ENDPOINT_INCOMPLETE_NO_REGION_MATCH, VALID_ABSENTEE_INITIAL
    )

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "esign_method": None,
        "ovbm_link": "mock-ovbm-link",
        "region": None,
        "regions": [],
        "allow_print_and_forward": True,
        #        "deliverable": True,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": None,
    }

    # bad address
    mock_verify_address.return_value = (False, {})
    response = client.patch(
        ABSENTEE_API_ENDPOINT_PATCH_INCOMPLETE.format(uuid=ballot_request.uuid),
        {
            "request_mailing_address1": "123 A St NW foo",
            "request_mailing_city": "Washington",
            "request_mailing_state": "DC",
            "request_mailing_zipcode": "20001",
            "region": 12345,
        },
    )

    assert response.status_code == 400
    assert "request_mailing_address1" in response.json()
    assert response.json()["request_mailing_deliverable_not_ignored"]

    # try to complete (and fail!) with undeliverable request_mailing_address
    response = client.patch(
        ABSENTEE_API_ENDPOINT_PATCH_COMPLETE.format(uuid=ballot_request.uuid),
        {
            "address1": "new_address",
            "region": 12345,
            "us_citizen": True,
            "is_18_or_over": True,
        },
    )

    assert response.status_code == 400
    assert "request_mailing_address1" in response.json()
    assert response.json()["request_mailing_deliverable_not_ignored"]
    process_ballot_request.assert_not_called()
    ballot_request = BallotRequest.objects.first()
    assert ballot_request.status != TurnoutActionStatus.PENDING

    # ignore_undeliverable and complete
    response = client.patch(
        ABSENTEE_API_ENDPOINT_PATCH_COMPLETE.format(uuid=ballot_request.uuid),
        {
            "ignore_undeliverable": True,
            "region": 12345,
            "us_citizen": True,
            "is_18_or_over": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(ballot_request.uuid),
        "action_id": str(ballot_request.action.pk),
        "esign_method": "self_print",
        "ovbm_link": "mock-ovbm-link",
        "region": 12345,
        "allow_print_and_forward": True,
        #        "deliverable": False,
        #        "mailing_deliverable": None,
        "request_mailing_deliverable": False,
    }

    mock_finish.delay.assert_called_once_with(ballot_request.action.pk)
    process_ballot_request.assert_called_with(ballot_request, None, True)


@pytest.mark.django_db
def test_complete_lob_disallow(
    mock_check_unfinished,
    mock_get_absentee_contact_info,
    mock_get_regions_for_address,
    mock_verify_address,
    feature_flag_on,
):
    mock_get_regions_for_address.return_value = (
        [baker.make_recipe("official.region", external_id=12345)],
        False,
    )

    client = APIClient()
    response = client.post(ABSENTEE_API_ENDPOINT_INCOMPLETE, VALID_ABSENTEE_INITIAL)
    assert response.status_code == 200
    assert "uuid" in response.json()

    ballot_request = BallotRequest.objects.first()
    assert response.json()["uuid"] == str(ballot_request.uuid)
    assert response.json()["allow_print_and_forward"] == False
    assert response.json()["request_mailing_deliverable"] == None
    assert ballot_request.status == TurnoutActionStatus.INCOMPLETE
    assert (
        Event.objects.filter(
            action=ballot_request.action, event_type=EventType.START
        ).count()
        == 1
    )

    # try to complete with request_mailing address
    status_response = client.patch(
        ABSENTEE_API_ENDPOINT_PATCH_COMPLETE.format(uuid=ballot_request.uuid),
        {
            "request_mailing_address1": "12 A St",
            "request_mailing_city": "Aurora",
            "request_mailing_state": "IL",
            "request_mailing_zipcode": "12345",
            "ignore_undeliverable": True,
            "region": 12345,
            "us_citizen": True,
            "is_18_or_over": True,
        },
    )
    assert status_response.status_code == 400
    ballot_request.refresh_from_db()
    assert str(ballot_request.uuid) == response.json()["uuid"]
    assert ballot_request.request_mailing_address1 is None
    assert ballot_request.request_mailing_city is None
    assert ballot_request.request_mailing_state is None
    assert ballot_request.request_mailing_zipcode is None
    mock_check_unfinished.apply_async.assert_called_once()


@pytest.mark.django_db
def test_complete_lob_disallow2(
    mock_get_absentee_contact_info,
    mock_get_regions_for_address,
    mock_verify_address,
    feature_flag_on,
    mock_check_unfinished,
):
    mock_get_regions_for_address.return_value = (
        [baker.make_recipe("official.region", external_id=12345)],
        False,
    )

    client = APIClient()
    ref = VALID_ABSENTEE_INITIAL.copy()
    ref["request_mailing_address1"] = "123 A St."
    response = client.post(ABSENTEE_API_ENDPOINT_INCOMPLETE, ref)
    assert response.status_code == 400

    ref["request_mailing_address1"] = ""
    response = client.post(ABSENTEE_API_ENDPOINT_INCOMPLETE, ref)
    assert response.status_code == 200


# Test confirmation link that sends the actual letter
@pytest.mark.django_db
def test_lob_confirm(mocker):
    ballot_request = baker.make_recipe(
        "absentee.ballot_request",
        result_item_mail=baker.make_recipe("storage.ballot_request_form"),
    )

    send_date = datetime.datetime(2020, 1, 1, 1, 1, 1)
    send = mocker.patch("absentee.api_views.send_letter", return_value=send_date)

    client = APIClient()
    response = client.put(
        LOB_LETTER_CONFIRM_API_ENDPOINT.format(
            uuid=ballot_request.action.uuid, token=generate_lob_token(ballot_request)
        ),
    )

    send.assert_called_once_with(ballot_request, double_sided=True)
    assert response.json() == {"send_date": send_date.isoformat()}


@pytest.mark.django_db
def test_lob_confirm_dne(mocker):
    client = APIClient()

    response = client.put(
        LOB_LETTER_CONFIRM_API_ENDPOINT.format(
            uuid="7e6abe5f-7cc7-4d9a-96f1-75c9e6c05ed8", token="bar",
        )
    )
    assert response.status_code == 404
