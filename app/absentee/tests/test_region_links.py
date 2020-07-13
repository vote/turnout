import os

import pytest
from model_bakery import baker

from absentee.models import BallotRequest, RegionOVBMLink
from absentee.region_links import (
    FL_OVBM_LINK_PAGE,
    USER_AGENT,
    ovbm_link_for_ballot_request,
    refresh_region_links,
)
from absentee.tests.fixtures.florida_regions import florida_regions
from common.enums import StateFieldFormats
from election.models import StateInformation, StateInformationFieldType


@pytest.mark.django_db(transaction=True)
def test_region_links(florida_regions, requests_mock):
    with open(
        os.path.join(os.path.dirname(__file__), "fixtures/florida_ovbm_links.html"),
        "r",
    ) as f:
        html_response = f.read()

    requests_mock.register_uri(
        "GET",
        FL_OVBM_LINK_PAGE,
        text=html_response,
        request_headers={"Accept": "*/*", "User-Agent": USER_AGENT,},
    )

    refresh_region_links()

    created_links = {l.region.external_id: l.url for l in RegionOVBMLink.objects.all()}

    assert len(created_links) == len(florida_regions)

    # Test a few samples (Hentry and St. Johns)
    assert created_links[430678] == "https://hendry.electionsfl.org/vrservices/mbrs"
    assert created_links[430711] == "https://stjohns.electionsfl.org/vrservices/mbrs"


@pytest.mark.django_db
def test_ovbm_link_for_ballot_request():
    stateA = baker.make_recipe("election.state", code="AA")
    stateB = baker.make_recipe("election.state", code="BB")

    regionA1 = baker.make_recipe("official.region", state=stateA)
    regionA2 = baker.make_recipe("official.region", state=stateA)

    # Set a statewide URL for stateA
    ft = StateInformationFieldType(
        slug="external_tool_vbm_application", field_format=StateFieldFormats.URL
    )
    ft.save()

    infoA = StateInformation.objects.get(state=stateA, field_type=ft)
    infoA.text = "https://example.com/state_link"
    infoA.save()

    infoB = StateInformation.objects.get(state=stateB, field_type=ft)
    infoB.delete()

    # Set a region URL for regionA1
    region_link = RegionOVBMLink(region=regionA1, url="https://example.com/region_link")
    region_link.save()

    # region link
    assert (
        ovbm_link_for_ballot_request(BallotRequest(region=regionA1, state=stateA))
        == "https://example.com/region_link"
    )

    assert (
        ovbm_link_for_ballot_request(BallotRequest(region=regionA1, state=stateB))
        == "https://example.com/region_link"
    )

    # state link
    assert (
        ovbm_link_for_ballot_request(BallotRequest(region=regionA2, state=stateA))
        == "https://example.com/state_link"
    )

    assert (
        ovbm_link_for_ballot_request(BallotRequest(state=stateA))
        == "https://example.com/state_link"
    )

    # neither
    assert (
        ovbm_link_for_ballot_request(BallotRequest(region=regionA2, state=stateB))
        is None
    )

    assert ovbm_link_for_ballot_request(BallotRequest(state=stateB)) is None
