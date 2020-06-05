from unittest.mock import MagicMock

import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from absentee.models import BallotRequest
from common.enums import SubmissionType

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


# Incomplete create, matching region
@pytest.mark.django_db
def test_incomplete_create_single_matching_region(
    mock_get_absentee_contact_info, mock_get_regions_for_address
):
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        vbm_submission_type=SubmissionType.LEO_FAX,
    )

    mock_get_absentee_contact_info.return_value = MagicMock(fax="+16175551234")
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
        "esign_method": "leo_fax",
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
    mock_get_absentee_contact_info, mock_get_regions_for_address
):
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        vbm_submission_type=SubmissionType.LEO_EMAIL,
    )

    mock_get_absentee_contact_info.return_value = MagicMock(email="foo@example.com")
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


@pytest.mark.django_db
def test_incomplete_create_single_matching_region_missing_fax(
    mock_get_absentee_contact_info, mock_get_regions_for_address
):
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        vbm_submission_type=SubmissionType.LEO_FAX,
    )

    mock_get_absentee_contact_info.return_value = MagicMock(fax=None)
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


@pytest.mark.django_db
def test_incomplete_create_single_matching_region_missing_email(
    mock_get_absentee_contact_info, mock_get_regions_for_address
):
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        vbm_submission_type=SubmissionType.LEO_EMAIL,
    )

    mock_get_absentee_contact_info.return_value = MagicMock(email=None)
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


# Incomplete create, region matching error
@pytest.mark.django_db
def test_incomplete_create_region_matching_error(
    mock_get_absentee_contact_info, mock_get_regions_for_address
):
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        vbm_submission_type=SubmissionType.LEO_FAX,
    )

    baker.make_recipe("official.region", state=state, name="B", external_id=2)
    baker.make_recipe("official.region", state=state, name="C", external_id=3)
    baker.make_recipe("official.region", state=state, name="A", external_id=1)

    mock_get_absentee_contact_info.return_value = MagicMock(fax="+16175551234")
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
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        vbm_submission_type=SubmissionType.LEO_FAX,
    )

    baker.make_recipe("official.region", state=state, name="B", external_id=2)
    baker.make_recipe("official.region", state=state, name="C", external_id=3)
    baker.make_recipe("official.region", state=state, name="A", external_id=1)

    mock_get_absentee_contact_info.return_value = MagicMock(fax="+16175551234")
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
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        vbm_submission_type=SubmissionType.LEO_FAX,
    )

    r1 = baker.make_recipe("official.region", state=state, name="B", external_id=2)
    r2 = baker.make_recipe("official.region", state=state, name="C", external_id=3)
    baker.make_recipe("official.region", state=state, name="A", external_id=1)

    mock_get_absentee_contact_info.return_value = MagicMock(fax="+16175551234")
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
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        vbm_submission_type=SubmissionType.LEO_FAX,
    )

    r1 = baker.make_recipe("official.region", state=state, name="B", external_id=2)
    baker.make_recipe("official.region", state=state, name="C", external_id=3)
    baker.make_recipe("official.region", state=state, name="A", external_id=1)

    mock_get_absentee_contact_info.return_value = MagicMock(fax="+16175551234")
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
):
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        vbm_submission_type=SubmissionType.LEO_FAX,
    )

    mock_get_absentee_contact_info.return_value = MagicMock(fax="+16175551234")
    mock_get_regions_for_address.return_value = (
        [baker.make_recipe("official.region", external_id=12345)],
        False,
    )

    mock_get_absentee_contact_info.return_value = MagicMock(fax="+16175551234")

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
def test_incomplete_update_with_esign_filling(mock_get_absentee_contact_info):
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        vbm_submission_type=SubmissionType.LEO_FAX,
    )
    baker.make_recipe("official.region", external_id=12345)

    mock_get_absentee_contact_info.return_value = MagicMock(fax="+16175551234")

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

    print(response.json())

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
    mock_get_absentee_contact_info, process_ballotrequest_submission_task
):
    state = baker.make_recipe(
        "election.state",
        code=VALID_ABSENTEE_INITIAL["state"],
        vbm_submission_type=SubmissionType.LEO_FAX,
    )
    baker.make_recipe("official.region", external_id=12345)

    mock_get_absentee_contact_info.return_value = MagicMock(fax="+16175551234")

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
