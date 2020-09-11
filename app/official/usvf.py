# This code pulls down a copy of the USVF region office and contact
# data to our database, and does some validation on that data to
# ensure VBM contact data is complete for states that need it.
import logging
from enum import Enum as PythonEnum
from typing import Any, Dict, List, Sequence, Tuple

import phonenumbers
import requests
from django.conf import settings
from django.contrib.gis.geos import Point

from absentee.models import LeoContactOverride
from common import enums
from common.analytics import statsd
from common.apm import tracer
from common.geocode import geocode
from election.models import State

from .models import Address, Office, Region

API_ENDPOINT = "https://api.usvotefoundation.org/eod/v3"

logger = logging.getLogger("official")


def authenticated_session() -> requests.Session:
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry

    session = requests.Session()
    session.headers["Authorization"] = f"OAuth {settings.USVOTEFOUNDATION_KEY}"
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(
                total=5,
                status_forcelist=[500, 502, 503, 504],
                method_whitelist=["HEAD", "GET"],
            )
        ),
    )
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


@tracer.wrap()
def scrape_regions(session: requests.Session) -> List[Region]:
    session = authenticated_session()
    regions: List[Region] = []
    supported_states = State.states.values_list("code", flat=True)

    # The USVF API is buggy and does not paginate reliably.  Make
    # multiple passes with different page sizes to ensure we capture
    # all records.  In practice, the [100,73] is sufficient but
    # additional passes act as an insurance policy.
    saw_id = set()
    for limit in [100, 73, 67]:
        next_url = f"{API_ENDPOINT}/regions?limit={limit}"
        while next_url:
            with statsd.timed("turnout.official.usvfcall.regions", sample_rate=0.2):
                result = acquire_data(session, next_url)

            for usvf_region in result["objects"]:
                if usvf_region.get("state_abbr") not in supported_states:
                    continue

                id_ = usvf_region.get("id")
                if id_ in saw_id:
                    continue
                saw_id.add(id_)
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
        logger.info(
            "Found %(number)s Regions after this pass", {"number": len(regions)}
        )

    statsd.gauge("turnout.official.scraper.regions", len(regions))
    logger.info("Found %(number)s Regions", {"number": len(regions)})
    Region.objects.bulk_create(regions, ignore_conflicts=True)
    Region.objects.exclude(external_id__in=[r.external_id for r in regions]).delete()

    return regions


class Action(PythonEnum):
    INSERT = "Insert"
    UPDATE = "Update"


@tracer.wrap()
def scrape_offices(session: requests.Session, regions: Sequence[Region]) -> None:
    existing_region_ids = [region.external_id for region in regions]

    existing_offices = Office.objects.values_list("external_id", flat=True)
    offices_dict: Dict[(int, Tuple[Action, Office])] = {}

    existing_addresses = {a.external_id: a for a in Address.objects.all()}
    addresses_dict: Dict[(int, Tuple[Action, Address])] = {}

    # The USVF API pagination is buggy; make multiple passes with
    # different page sizes.
    for limit in [100, 73, 67]:
        next_url = f"{API_ENDPOINT}/offices?limit={limit}"
        while next_url:
            with statsd.timed("turnout.official.usvfcall.offices", sample_rate=0.2):
                result = acquire_data(session, next_url)

            for office in result["objects"]:
                # Check that the region is valid (we don't support US territories)
                region_id = int(office["region"].rsplit("/", 1)[1])
                if region_id not in existing_region_ids:
                    continue

                office_id = office["id"]
                if office_id in offices_dict:
                    continue

                # Process each office in the response
                if office_id in existing_offices:
                    office_action = Action.UPDATE
                else:
                    office_action = Action.INSERT
                offices_dict[office_id] = (
                    office_action,
                    Office(
                        external_id=office_id,
                        region_id=int(office["region"].split("/")[-1]),
                        hours=office.get("hours"),
                        notes=office.get("notes"),
                    ),
                )

                for address in office.get("addresses", []):
                    # Process each address in the office
                    existing = existing_addresses.get(address["id"], None)
                    if existing:
                        address_action = Action.UPDATE
                        location = existing.location
                    else:
                        address_action = Action.INSERT
                        location = None
                    if not location and settings.USVF_GEOCODE:
                        addrs = geocode(
                            street=address.get("street1"),
                            city=address.get("city"),
                            state=address.get("state"),
                            zipcode=address.get("zip"),
                        )
                        if addrs:
                            location = Point(
                                addrs[0]["location"]["lng"], addrs[0]["location"]["lat"]
                            )
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
                            location=location,
                            is_physical=address.get("is_physical"),
                            is_regular_mail=address.get("is_regular_mail"),
                            process_domestic_registrations="DOM_VR"
                            in address["functions"],
                            process_absentee_requests="DOM_REQ" in address["functions"],
                            process_absentee_ballots="DOM_RET" in address["functions"],
                            process_overseas_requests="OVS_REQ" in address["functions"],
                            process_overseas_ballots="OVS_RET" in address["functions"],
                        ),
                    )

            next_url = result["meta"].get("next")
        logger.info(
            "Found %(number)s offices after this pass", {"number": len(offices_dict)}
        )

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
            "location",
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


def check_state_contacts(state_id: str, mode: enums.SubmissionType) -> str:
    if mode not in [enums.SubmissionType.LEO_EMAIL, enums.SubmissionType.LEO_FAX]:
        return None

    regions: Dict[int, Region] = {
        region.external_id: region
        for region in Region.objects.filter(state_id=state_id)
    }
    region_offices: Dict[int, List[Office]] = {
        region_id: [] for region_id in regions.keys()
    }
    office_addresses: Dict[int, List[Address]] = {}
    for office in Office.objects.filter(region_id__in=regions.keys()):
        region_offices[office.region_id].append(office)
        office_addresses[office.external_id] = []

    for address in Address.objects.filter(office_id__in=office_addresses.keys()):
        office_addresses[address.office_id].append(address)

    region_override = {}
    for override in LeoContactOverride.objects.filter(region_id__in=regions.keys()):
        region_override[override.region_id] = override

    bad_regions = []
    for region_id, region in regions.items():
        num = 0
        override = region_override.get(region_id)
        for office in region_offices[region_id]:
            for address in office_addresses[office.external_id]:
                if mode == enums.SubmissionType.LEO_FAX and (
                    (address.fax and phonenumbers.is_valid_number(address.fax))
                    or (override and override.fax)
                ):
                    num += 1
                if mode == enums.SubmissionType.LEO_EMAIL and (
                    address.email or (override and override.email)
                ):
                    num += 1

        if not num:
            url = f"https://www.voteamerica.com/local-election-offices/{state_id}/{region.external_id}/"
            m = f"    {region_id} {region.name} ({state_id}) - {url}"
            bad_regions.append(m)

    if bad_regions:
        message = (
            f"{state_id} has {len(bad_regions)} regions missing {mode} contact info"
        )
        return "\n".join([message] + bad_regions)
    return None


@tracer.wrap()
def check_vbm_states():
    # TODO: bring this back in some form? Now that we have clean fallbacks for
    # missing contact info maybe we don't need it?
    pass
    # for state in State.objects.all():
    #     if state.vbm_submission_type != enums.SubmissionType.SELF_PRINT:
    #         message = check_state_contacts(state.code, state.vbm_submission_type)
    #         if message:
    #             logger.warning(message)
    #             if settings.SLACK_DATA_ERROR_ENABLED:
    #                 try:
    #                     with statsd.timed(
    #                         "turnout.official.check_vbm_states.slackcall"
    #                     ):
    #                         r = requests.post(
    #                             settings.SLACK_DATA_ERROR_WEBHOOK,
    #                             json={"text": message},
    #                         )
    #                     r.raise_for_status()
    #                 except Exception as e:
    #                     logger.warning(f"Failed to post warning to slack webhook: {e}")
