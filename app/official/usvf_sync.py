# This code pulls the bare minimum necessary from the US Vote Foundation API for
# local usage. The goal is to reduce the number of hits on the API and our database
import logging
from enum import Enum as PythonEnum
from typing import Any, Dict, List, Sequence, Tuple

import requests
from django.conf import settings

from common.analytics import statsd
from election.models import State

from .models import Address, Office, Region

API_ENDPOINT = "https://api.usvotefoundation.org/eod/v3"

logger = logging.getLogger("official")


def authenticated_session() -> requests.Session:
    session = requests.Session()
    session.headers["Authorization"] = f"OAuth {settings.USVOTEFOUNDATION_KEY}"
    return session


def acquire_data(session: requests.Session, url: str) -> Dict[(str, Any)]:
    response = session.get(url)
    extra = {"url": response.request.url, "status_code": response.status_code}
    if response.status_code != 200:
        logger.warning(
            "Error pulling region via url %(url)s. Code: %(status_code)s",
            extra,
            extra=extra,
        )
        raise requests.RequestException(request=response.request, response=response)
    else:
        logger.info(
            "Pulled from URL %(url)s. Code: %(status_code)s", extra, extra=extra
        )
    return response.json()


@statsd.timed("turnout.official.scrape_region")
def scrape_regions(session: requests.Session) -> List[Region]:
    session = authenticated_session()
    regions: List[Region] = []
    supported_states = State.objects.values_list("code", flat=True)

    next_url = f"{API_ENDPOINT}/regions?limit=100"
    while next_url:
        with statsd.timed("turnout.official.usvfcall.regions", sample_rate=0.2):
            result = acquire_data(session, next_url)

        for usvf_region in result["objects"]:
            if usvf_region.get("state_abbr") not in supported_states:
                continue
            regions.append(
                Region(
                    external_id=usvf_region["id"],
                    name=usvf_region.get("region_name"),
                    municipality=usvf_region.get("municipality_name"),
                    municipality_type=usvf_region.get("municipality_type"),
                    county=usvf_region.get("county_name"),
                    state_id=usvf_region.get("state_abbr"),
                )
            )

        next_url = result["meta"].get("next")

    statsd.gauge("turnout.official.scraper.regions", len(regions))
    logger.info("Found %(number)s Regions", {"number": len(regions)})
    Region.objects.bulk_create(regions, ignore_conflicts=True)
    Region.objects.exclude(external_id__in=[r.external_id for r in regions]).delete()

    return regions


class Action(PythonEnum):
    INSERT = "Insert"
    UPDATE = "Update"


@statsd.timed("turnout.official.scrape_offices")
def scrape_offices(session: requests.Session, regions: Sequence[Region]) -> None:
    existing_region_ids = [region.external_id for region in regions]

    existing_offices = Office.objects.values_list("external_id", flat=True)
    offices_dict: Dict[(int, Tuple[Action, Office])] = {}

    existing_addresses = Address.objects.values_list("external_id", flat=True)
    addresses_dict: Dict[(int, Tuple[Action, Address])] = {}

    next_url = f"{API_ENDPOINT}/offices?limit=100"
    while next_url:
        with statsd.timed("turnout.official.usvfcall.offices", sample_rate=0.2):
            result = acquire_data(session, next_url)

        for office in result["objects"]:
            # Check that the region is valid (we don't support US territories)
            region_id = int(office["region"].rsplit("/", 1)[1])
            if region_id not in existing_region_ids:
                continue

            # Process each office in the response
            if office["id"] in existing_offices:
                office_action = Action.UPDATE
            else:
                office_action = Action.INSERT
            offices_dict[office["id"]] = (
                office_action,
                Office(
                    external_id=office["id"],
                    region_id=int(office["region"].split("/")[-1]),
                    hours=office.get("hours"),
                    notes=office.get("notes"),
                ),
            )

            for address in office.get("addresses", []):
                # Process each address in the office
                if address["id"] in existing_addresses:
                    address_action = Action.UPDATE
                else:
                    address_action = Action.INSERT
                addresses_dict[address["id"]] = (
                    address_action,
                    Address(
                        external_id=address["id"],
                        office_id=office["id"],
                        address=address.get("address_to"),
                        address2=address.get("street1"),
                        address3=address.get("street2"),
                        city=address.get("city"),
                        state_id=address.get("state"),
                        zipcode=address.get("zip"),
                        website=address.get("website"),
                        email=address.get("main_email"),
                        phone=address.get("main_phone_number"),
                        fax=address.get("main_fax_number"),
                        is_physical=address.get("is_physical"),
                        is_regular_mail=address.get("is_regular_mail"),
                        process_domestic_registrations="DOM_VR" in address["functions"],
                        process_absentee_requests="DOM_REQ" in address["functions"],
                        process_absentee_ballots="DOM_RET" in address["functions"],
                        process_overseas_requests="OVS_REQ" in address["functions"],
                        process_overseas_ballots="OVS_RET" in address["functions"],
                    ),
                )

        next_url = result["meta"].get("next")

    statsd.gauge("turnout.official.scraper.offices", len(offices_dict))
    logger.info("Found %(number)s Offices", {"number": len(offices_dict)})
    statsd.gauge("turnout.official.scraper.addresses", len(addresses_dict))
    logger.info("Found %(number)s Addresses", {"number": len(addresses_dict)})

    # Remove any records in our database but not in the result
    Office.objects.exclude(external_id__in=offices_dict.keys()).delete()
    Address.objects.exclude(external_id__in=addresses_dict.keys()).delete()

    # Create any records that are not already in our database
    Office.objects.bulk_create(
        [x[1] for x in offices_dict.values() if x[0] == Action.INSERT]
    )
    Address.objects.bulk_create(
        [x[1] for x in addresses_dict.values() if x[0] == Action.INSERT]
    )

    # Update any records that are already in our database
    Office.objects.bulk_update(
        [x[1] for x in offices_dict.values() if x[0] == Action.UPDATE],
        ["hours", "notes"],
    )
    Address.objects.bulk_update(
        [x[1] for x in addresses_dict.values() if x[0] == Action.UPDATE],
        [
            "address",
            "address2",
            "address3",
            "city",
            "state",
            "zipcode",
            "website",
            "email",
            "phone",
            "fax",
            "is_physical",
            "is_regular_mail",
            "process_domestic_registrations",
            "process_absentee_requests",
            "process_absentee_ballots",
            "process_overseas_requests",
            "process_overseas_ballots",
        ],
    )


def sync() -> None:
    session = requests.Session()
    session.headers["Authorization"] = f"OAuth {settings.USVOTEFOUNDATION_KEY}"
    regions = scrape_regions(session)
    scrape_offices(session, regions)
