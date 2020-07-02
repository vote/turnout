import logging

import requests
from django.conf import settings

from election.models import StateInformation

logger = logging.getLogger("integration")

MONITORS = {
    "polling-place": "external_tool_polling_place",
    "ovr": "external_tool_ovr",
    "verify-status": "external_tool_verify_status",
    "absentee-application": "external_tool_vbm_application",
    "absentee-tracker": "external_tool_absentee_ballot_tracker",
}

CHECKS_ENDPOINT = "https://uptime.com/api/v1/checks/"
ADD_ENDPOINT = "https://uptime.com/api/v1/checks/add-http/"
STATUSPAGES_ENDPOINT = "https://uptime.com/api/v1/statuspages/"


def get_existing():
    checks = {}
    nexturl = CHECKS_ENDPOINT
    while nexturl:
        response = requests.get(
            nexturl, headers={"Authorization": f"Token {settings.UPTIMEDOTCOM_KEY}"},
        )
        for test in response.json()["results"]:
            checks[test["name"]] = test
        nexturl = response.json().get("next")

    pages = {}
    response = requests.get(
        STATUSPAGES_ENDPOINT,
        headers={"Authorization": f"Token {settings.UPTIMEDOTCOM_KEY}"},
    )
    for page in response.json()["results"]:
        pages[page["name"]] = page

    return checks, pages


def update_group(prefix, slug, existing):
    names = []
    for item in StateInformation.objects.filter(field_type__slug=slug):
        # some values are blank
        if not item.text:
            continue

        name = f"{prefix}-{item.state_id}"
        names.append(name)

        req = {
            "name": name,
            # hack: uptime.com uppercases urlescaped hex, so uppercase our value too to avoid a diff
            "msp_address": item.text.replace("%2f", "%2F"),
            "msp_interval": 10,
            "contact_groups": ["Default"],
            "locations": ["US East", "US West", "US Central",],
        }

        if name in existing:
            old = existing[name]
            del existing[name]

            same = True
            for k, v in req.items():
                if v != old.get(k):
                    logger.info(f"{name} field {old[k]} != {v}")
                    same = False
            if same:
                continue

            logger.info(f"Updating {name}")
            response = requests.patch(
                f"{CHECKS_ENDPOINT}{old['pk']}/",
                headers={"Authorization": f"Token {settings.UPTIMEDOTCOM_KEY}"},
                json=req,
            )
        else:
            logger.info(f"Adding {name} {item.text}")
            req["type"] = "http"
            response = requests.post(
                ADD_ENDPOINT,
                headers={"Authorization": f"Token {settings.UPTIMEDOTCOM_KEY}"},
                json=req,
            )
        if response.status_code != 200:
            logger.warning(response.text)

    for name, old in existing.items():
        if name.startswith(prefix + "-"):
            logger.info(f"Removing {name}")
            response = requests.delete(
                f"{CHECKS_ENDPOINT}{old['pk']}/",
                headers={"Authorization": f"Token {settings.UPTIMEDOTCOM_KEY}"},
            )

    return names


def sync():
    checks, pages = get_existing()

    for prefix, slug in MONITORS.items():
        names = update_group(prefix, slug, checks)

        if len(names) > 50:
            # Ugh, uptime.com limit of 50.  Let's drop DC.
            names = [n for n in names if not n.endswith("DC")]

        page_slug = f"voteamerica-{prefix}"
        req = {
            "name": prefix,
            "slug": page_slug,
            "services": names,
            "is_public": True,
            "allow_search_indexing": True,
            "allow_drill_down": True,
            "allow_subscriptions": True,
        }

        if prefix in pages:
            old = pages[prefix]
            same = True
            for k, v in req.items():
                if v != old[k]:
                    same = False
            if same:
                continue
            logger.info(f"Updating page {prefix} {page_slug}")
            response = requests.patch(
                f"{STATUSPAGES_ENDPOINT}{pages[prefix]['pk']}/",
                headers={"Authorization": f"Token {settings.UPTIMEDOTCOM_KEY}"},
                json=req,
            )
        else:
            logger.info(f"Creating page {prefix} {page_slug} services {names}")
            response = requests.post(
                f"{STATUSPAGES_ENDPOINT}",
                headers={"Authorization": f"Token {settings.UPTIMEDOTCOM_KEY}"},
                json=req,
            )
        if response.status_code != 200:
            logger.warning(response.text)
