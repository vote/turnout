from uuid import UUID

import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from action.models import Action
from multi_tenant.models import Client
from polling_place.models import PollingPlaceLookup

PP_API_ENDPOINT = "/v1/pollingplace/report/"
VALID_LOOKUP = {
    "unstructured_address": "1234 spruce st., philadelphia, PA 19103",
    "embed_url": "https://www.greatvoter.com/location/of/embed",
    "session_id": "7293d330-3216-439b-aa1a-449c7c458ebe",
    "dnc_result": {
        "data": {
            "confidence_score": "1.0",
            "county": "Philadelphia",
            "dropbox_locations": [
                {
                    "address_line_1": "1400 John F Kennedy Blvd., Room 142",
                    "city": "Philadelphia",
                    "dates_hours": "9/14-11/03 Days/Time TBD",
                    "lat": 39.95348,
                    "location_id": "8651581590675772134",
                    "location_name": "Philadelphia County Board of Elections (City Hall)",
                    "lon": -75.163328,
                    "open_early_voting": True,
                    "open_election_day": True,
                    "source": "dnc",
                    "state": "PA",
                    "zip": "19107",
                },
                {
                    "address_line_1": "520 N Columbus Blvd, 5th Floor",
                    "city": "Philadelphia",
                    "dates_hours": "9/14-11/03 Days/Time TBD",
                    "lat": 39.976822,
                    "location_id": "8560403970394187782",
                    "location_name": "Philadelphia County Board of Elections (Spring Garden)",
                    "lon": -75.144155,
                    "open_early_voting": True,
                    "open_election_day": True,
                    "source": "dnc",
                    "state": "PA",
                    "zip": "19123",
                },
            ],
            "early_vote_locations": [
                {
                    "address_line_1": "1400 John F Kennedy Blvd., Room 142",
                    "city": "Philadelphia",
                    "dates_hours": "9/14-11/03 Days/Time TBD",
                    "lat": 39.95348,
                    "location_id": "1961415530018472419",
                    "location_name": "Philadelphia County Board of Elections (City Hall)",
                    "lon": -75.163328,
                    "source": "dnc",
                    "state": "PA",
                    "zip": "19107",
                },
                {
                    "address_line_1": "520 N Columbus Blvd, 5th Floor",
                    "city": "Philadelphia",
                    "dates_hours": "9/14-11/03 Days/Time TBD",
                    "lat": 39.976822,
                    "location_id": "8926882933896705715",
                    "location_name": "Philadelphia County Board of Elections (Spring Garden)",
                    "lon": -75.144155,
                    "source": "dnc",
                    "state": "PA",
                    "zip": "19123",
                },
            ],
            "election_day_locations": [
                {
                    "address_line_1": "17th & Spruce Sts",
                    "city": "Philadelphia",
                    "dates_hours": "7am-8pm",
                    "lat": 39.947579,
                    "location_id": "3016210073558717281",
                    "location_name": "08/04 TENTH PRESBYTERIAN CHURCH",
                    "lon": -75.169613,
                    "source": "dnc",
                    "state": "PA",
                    "zip": "19103",
                }
            ],
            "home_address": {
                "address_line_1": "1234 Spruce St",
                "city": "Philadelphia",
                "state": "PA",
                "zip": "19103",
            },
            "mail_ballot_info": {
                "dropoff_by": "2020-11-03",
                "postmark_by": None,
                "qualified_request": False,
                "receive_by": "2020-11-03",
                "request_by": "2020-10-27",
                "requires_request": True,
                "url": {
                    "en": "iwillvote.com/votebymail?state=PA",
                    "es": "voyavotar.com/votebymail?state=PA",
                },
            },
            "precinct_code": "Philadelphia 08-04",
            "precinct_id": "376611",
            "state": "PA",
            "status": "success",
        },
    },
}


def test_get_request_disallowed():
    client = APIClient()
    response = client.get(PP_API_ENDPOINT)
    assert response.status_code == 405
    assert response.json() == {"detail": 'Method "GET" not allowed.'}


def test_blank_api_request(requests_mock):
    client = APIClient()
    response = client.post(PP_API_ENDPOINT, {}, format="json")
    assert response.status_code == 400
    expected_response = {
        "unstructured_address": ["This field is required."],
    }
    assert response.json() == expected_response


@pytest.mark.django_db
def test_blank_dnc_result(requests_mock):
    client = APIClient()
    response = client.post(
        PP_API_ENDPOINT,
        {"unstructured_address": "foo", "dnc_result": None,},
        format="json",
    )
    print(response.json())
    assert response.status_code == 200
    action = Action.objects.first()
    assert response.json() == {"action_id": str(action.pk)}


@pytest.mark.django_db
def test_object_created(mocker):
    baker.make_recipe("election.state", code="PA")
    client = APIClient()
    response = client.post(PP_API_ENDPOINT, VALID_LOOKUP, format="json")
    assert response.status_code == 200
    action = Action.objects.first()
    assert response.json() == {"action_id": str(action.pk)}

    assert PollingPlaceLookup.objects.count() == 1
    lookup = PollingPlaceLookup.objects.first()

    assert lookup.unstructured_address == VALID_LOOKUP["unstructured_address"]
    assert lookup.dnc_result == VALID_LOOKUP["dnc_result"]
    assert lookup.dnc_status == VALID_LOOKUP["dnc_result"]["data"]["status"]
    assert lookup.address1 == "1234 Spruce St"
    assert lookup.city == "Philadelphia"
    assert lookup.state_id == "PA"
    assert lookup.zipcode == "19103"
    assert lookup.embed_url == "https://www.greatvoter.com/location/of/embed"
    assert lookup.session_id == UUID("7293d330-3216-439b-aa1a-449c7c458ebe")
    first_subscriber = Client.objects.first()
    assert lookup.subscriber == first_subscriber
