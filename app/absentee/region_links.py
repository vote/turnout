import re
import urllib.parse
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from django.db import transaction

from common.rollouts import get_feature
from election.models import StateInformation
from official.models import Region

from .models import BallotRequest, RegionOVBMLink

FL_OVBM_LINK_PAGE = "https://fl.dems.vote/mail/"

# FL website blocks unknown or missing user-agents
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"


def normalize_county_name(name: str) -> str:
    """
    Normalizes different spellings of the same county (e.g. De Soto vs. DESOTO,
    ST. JOHNS vs. Saint Johns)
    """
    return re.sub("[^a-z]", "", name.strip().lower().replace("saint", "st"))


def get_florida_data() -> List[RegionOVBMLink]:
    # Build a mapping of County -> region ID
    county_to_region = {
        normalize_county_name(r.county): r for r in Region.visible.filter(state="FL")
    }

    r = requests.get(
        FL_OVBM_LINK_PAGE, headers={"Accept": "*/*", "User-Agent": USER_AGENT},
    )

    if r.status_code != 200:
        raise RuntimeError(f"Invalid status code: {r.status_code}")

    soup = BeautifulSoup(r.text, "html.parser")

    counties = []
    for row in soup.find("div", id="counties").find_all(
        "div", class_="nectar-hor-list-item"
    ):
        county_h5 = row.find("h5")
        if county_h5 is None:
            raise RuntimeError("A .nectar-hor-list-item was missing an h5")

        url_a = row.find("a", class_="full-link")
        if url_a is None:
            raise RuntimeError("A .nectar-hor-list-item was missing an a.full-link")

        county_name = normalize_county_name(county_h5.string)
        if county_name not in county_to_region:
            raise RuntimeError(
                f"Got a county that is not in the USVF data: {county_name}"
            )

        counties.append(
            RegionOVBMLink(region=county_to_region[county_name], url=url_a["href"])
        )

    if len(counties) != len(county_to_region):
        raise RuntimeError(
            f"Got {len(counties)} from the Florida website, but we have {len(county_to_region)} USVF regions"
        )

    return counties


def refresh_region_links():
    links = get_florida_data()

    with transaction.atomic():
        RegionOVBMLink.objects.filter(region__state__code="FL").delete()
        RegionOVBMLink.objects.bulk_create(links)


MOVOTE_PARAM_FULL_NAME = "field95899935"
MOVOTE_PARAM_DOB_M = "field95899936M"
MOVOTE_PARAM_DOB_D = "field95899936D"
MOVOTE_PARAM_DOB_Y = "field95899936Y"
MOVOTE_PARAM_ADDR12 = "field95899939"
MOVOTE_PARAM_ADDR_CITY = "field95899940"
MOVOTE_PARAM_ADDR_STATE = "field97542631"
MOVOTE_PARAM_ADDR_ZIPCODE = "field97542630"
MOVOTE_PARAM_PHONE = "field95899945"
MOVOTE_PARAM_EMAIL = "field95899946"

MOVOTE_BASE_URL = "https://movote.formstack.com/forms/november3absenteeballotrequest"


def build_movote_url(request: BallotRequest) -> str:
    params = {
        MOVOTE_PARAM_FULL_NAME: f"{request.first_name} {request.last_name}",
        MOVOTE_PARAM_DOB_M: request.date_of_birth.month,
        MOVOTE_PARAM_DOB_D: request.date_of_birth.day,
        MOVOTE_PARAM_DOB_Y: str(request.date_of_birth.year)[-2:],
        MOVOTE_PARAM_ADDR12: " ".join(
            [s for s in (request.address1, request.address2) if s]
        ),
        MOVOTE_PARAM_ADDR_CITY: request.city,
        MOVOTE_PARAM_ADDR_STATE: request.state_id,
        MOVOTE_PARAM_ADDR_ZIPCODE: request.zipcode,
        MOVOTE_PARAM_PHONE: str(request.phone) if request.phone else "",
        MOVOTE_PARAM_EMAIL: request.email,
    }

    return f"{MOVOTE_BASE_URL}?{urllib.parse.urlencode(params)}"


def ovbm_link_for_ballot_request(request: BallotRequest) -> Optional[str]:
    if get_feature("movote") and request.state and request.state.code == "MO":
        return build_movote_url(request)

    if request.region:
        region_link = RegionOVBMLink.objects.filter(region=request.region).first()
        if region_link:
            return region_link.url

    if request.state:
        state_link = StateInformation.objects.filter(
            field_type__slug="external_tool_vbm_application", state=request.state,
        ).first()
        if state_link and state_link.text:
            return state_link.text

    return None
