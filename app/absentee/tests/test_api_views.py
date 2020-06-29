import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from absentee.contactinfo import AbsenteeContactInfo
from absentee.models import BallotRequest
from common.enums import StateFieldFormats, SubmissionType
from election.models import StateInformation, StateInformationFieldType

ABSENTEE_API_ENDPOINT_INCOMPLETE = (
    "/v1/absentee/request/?incomplete=true&match_region=true"
)
ABSENTEE_API_ENDPOINT_INCOMPLETE_NO_REGION_MATCH = (
    "/v1/absentee/request/?incomplete=true"
)
ABSENTEE_API_ENDPOINT_COMPLETE = "/v1/absentee/request/"

ABSENTEE_API_ENDPOINT_PATCH_INCOMPLETE = "/v1/absentee/request/{uuid}/?incomplete=true"

ABSENTEE_API_ENDPOINT_PATCH_COMPLETE = "/v1/absentee/request/{uuid}/"

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
    "sms_opt_in": True,
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
    "sms_opt_in": True,
    "sms_opt_in_subscriber": True,
    "region": 12345,
    "us_citizen": True,
    "is_18_or_over": True,
}


@pytest.fixture
def mock_get_absentee_contact_info(mocker):
    return mocker.patch("absentee.api_views.get_absentee_contact_info")


@pytest.fixture
def mock_get_regions_for_address(mocker):
    return mocker.patch("absentee.api_views.get_regions_for_address")


@pytest.fixture
def process_ballotrequest_submission_task(mocker):
    return mocker.patch("absentee.api_views.process_ballotrequest_submission.delay")


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


# Incomplete create, matching region
@pytest.mark.django_db
def test_incomplete_create_single_matching_region(
    mock_get_absentee_contact_info, mock_get_regions_for_address, feature_flag_off
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
    mock_get_absentee_contact_info, mock_get_regions_for_address, feature_flag_on
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
    }


# Incomplete create, region matching error
@pytest.mark.django_db
def test_incomplete_create_region_matching_error(
    mock_get_absentee_contact_info, mock_get_regions_for_address
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
        "regions": [
            {"name": "A", "external_id": 1},
            {"name": "B", "external_id": 2},
            {"name": "C", "external_id": 3},
        ],
    }


# Incomplete create, no matching regions
@pytest.mark.django_db
def test_incomplete_create_no_matching_regions(
    mock_get_absentee_contact_info, mock_get_regions_for_address
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
        "regions": [
            {"name": "A", "external_id": 1},
            {"name": "B", "external_id": 2},
            {"name": "C", "external_id": 3},
        ],
    }


# Incomplete create, multiple matching regions
@pytest.mark.django_db
def test_incomplete_create_multiple_matching_regions(
    mock_get_absentee_contact_info, mock_get_regions_for_address
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
        "regions": [{"name": "B", "external_id": 2}, {"name": "C", "external_id": 3},],
    }


# Incomplete create, no region matching requested
@pytest.mark.django_db
def test_incomplete_create_no_region_matching(
    mock_get_absentee_contact_info, mock_get_regions_for_address
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
        "regions": [
            {"name": "A", "external_id": 1},
            {"name": "B", "external_id": 2},
            {"name": "C", "external_id": 3},
        ],
    }


# Complete create
@pytest.mark.django_db
def test_complete_create(
    mock_get_absentee_contact_info,
    mock_get_regions_for_address,
    process_ballotrequest_submission_task,
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
        "region": 12345,
    }

    assert ballot_request.region.external_id == 12345

    process_ballotrequest_submission_task.assert_called_with(
        ballot_request.pk, None, True
    )


# Incomplete update, not filling in esign method
@pytest.mark.django_db
def test_incomplete_update_no_esign_filling():
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
        "region": None,
    }

    assert BallotRequest.objects.count() == 1
    ballot_request_new = BallotRequest.objects.first()

    assert ballot_request_new.address1 == "new_address"


# Incomplete update, filling in esign method
@pytest.mark.django_db
def test_incomplete_update_with_esign_filling(
    mock_get_absentee_contact_info, feature_flag_on
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
        "region": 12345,
    }


# Complete update
@pytest.mark.django_db
def test_complete_update(
    mock_get_absentee_contact_info,
    process_ballotrequest_submission_task,
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
        "region": 12345,
    }

    process_ballotrequest_submission_task.assert_called_with(
        ballot_request.pk, None, True
    )


@pytest.mark.parametrize(
    "flag,email_allowed,fax_allowed,email_contact,fax_contact,expected",
    [
        # Flag on, email and fax allowed, both contact infos -> email
        (True, True, True, True, True, SubmissionType.LEO_EMAIL),
        # Flag off, email and fax allowed, both contact info -> self-print
        (False, True, True, True, True, SubmissionType.SELF_PRINT),
        # Flag on, email and fax allowed, only fax number -> fax
        (True, True, True, False, True, SubmissionType.LEO_FAX),
        # Flag on, email and fax allowed, no contact -> self-print
        (True, True, True, False, False, SubmissionType.SELF_PRINT),
        # Flag on, email allowed, fax number -> self-print
        (True, True, None, False, True, SubmissionType.SELF_PRINT),
        # Flag on, fax allowed, email and fax number -> fax
        (True, None, True, True, True, SubmissionType.LEO_FAX),
        # Flag on, email allowed, email -> email
        (True, True, None, True, False, SubmissionType.LEO_EMAIL),
        # Flag on, nothing allowed, both contact infos -> self-print
        (True, None, None, True, True, SubmissionType.SELF_PRINT),
        # Flag on, email and fax explicitly disallowed, both contact infos -> self-print
        (True, False, False, True, True, SubmissionType.SELF_PRINT),
        # Flag on, email disallowed, fax allowed, both contact infos -> fax
        (True, False, True, True, True, SubmissionType.LEO_FAX),
    ],
)
@pytest.mark.django_db
def test_get_esign_method(
    flag,
    email_allowed,
    fax_allowed,
    email_contact,
    fax_contact,
    expected,
    mocker,
    mock_get_absentee_contact_info,
    mock_get_regions_for_address,
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
        [baker.make_recipe("official.region", external_id=12345)],
        False,
    )

    contact_info = {}
    if email_contact:
        contact_info["email"] = "foo@example.com"
    if fax_contact:
        contact_info["fax"] = "+16175551234"

    mock_get_absentee_contact_info.return_value = AbsenteeContactInfo(**contact_info)

    # Run the test!
    client = APIClient()
    response = client.post(ABSENTEE_API_ENDPOINT_INCOMPLETE, VALID_ABSENTEE_INITIAL)

    assert BallotRequest.objects.count() == 1
    ballot_request = BallotRequest.objects.first()

    assert ballot_request.esign_method == expected
