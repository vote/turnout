import re
from typing import List, Optional

import requests
from django.db import transaction

from bs4 import BeautifulSoup
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
        normalize_county_name(r.county): r for r in Region.objects.filter(state="FL")
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
        RegionOVBMLink.objects.all().delete()
        RegionOVBMLink.objects.bulk_create(links)


def ovbm_link_for_ballot_request(request: BallotRequest) -> Optional[str]:
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
