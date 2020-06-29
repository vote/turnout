import copy
import logging

import datadog
import requests
from django.conf import settings

from election.models import StateInformation

logger = logging.getLogger("integration")

MONITORS = {
    "ovr": "external_tool_ovr",
    "polling-place": "external_tool_polling_place",
    "verify-status": "external_tool_verify_status",
    "absentee-application": "external_tool_vbm_application",
    "absentee-tracker": "external_tool_absentee_ballot_tracker",
}

TESTS_ENDPOINT = "https://api.datadoghq.com/api/v1/synthetics/tests"

CREATE_TEMPLATE = {
    "locations": ["aws:us-east-2", "aws:us-west-1", "aws:us-west-2"],
    "name": "...",
    "message": "",
    "config": {
        "request": {"url": "...", "method": "GET", "timeout": 30},
        "assertions": [{"operator": "is", "type": "statusCode", "target": 200}],
    },
    "type": "api",
    "options": {
        "monitor_options": {
            "notify_audit": False,
            "locked": False,
            "include_tags": True,
            "new_host_delay": 300,
            "notify_no_data": False,
            "renotify_interval": 0,
        },
        "retry": {"count": 0, "interval": 300},
        "min_location_failed": 1,
        "min_failure_duration": 0,
        "tick_every": 300,
    },
    "tags": ["env:external"],
}


def get_existing_synthetics():
    r = {}
    for test in datadog.api.Synthetics.get_all_tests()["tests"]:
        r[test["name"]] = test
    return r


def update_group(prefix, slug, existing):
    for item in StateInformation.objects.filter(field_type__slug=slug):
        # some values are blank
        if not item.text:
            continue

        name = f"{prefix}-{item.state_id}"

        req = copy.deepcopy(CREATE_TEMPLATE)
        req["name"] = name
        req["config"]["request"]["url"] = item.text
        req["tags"].append(f"type:{prefix}")

        if name in existing:
            old = existing[name]
            del existing[name]
            same = True
            for k in ["options", "config", "name", "locations", "tags"]:
                if old[k] != req[k]:
                    same = False
            if same:
                continue
            logger.info(f"Updating {name}")
            response = requests.put(
                f"{TESTS_ENDPOINT}/{old['public_id']}",
                headers={
                    "DD-API-KEY": settings.DATADOG_API_KEY,
                    "DD-APPLICATION-KEY": settings.DATADOG_APPLICATION_KEY,
                },
                json=req,
            )
        else:
            logger.info(f"Adding {name} {item.text}")
            response = requests.post(
                TESTS_ENDPOINT,
                headers={
                    "DD-API-KEY": settings.DATADOG_API_KEY,
                    "DD-APPLICATION-KEY": settings.DATADOG_APPLICATION_KEY,
                },
                json=req,
            )
        if response.status_code != 200:
            logger.warning(response.text)

    for name, old in existing.items():
        if name.startswith(prefix + "-"):
            logger.info(f"Removing {name}")
            datadog.api.Synthetics.delete_test(public_ids=[old["public_id"]])


def sync():
    datadog.initialize(
        api_key=settings.DATADOG_API_KEY, app_key=settings.DATADOG_APPLICATION_KEY,
    )
    existing = get_existing_synthetics()
    for prefix, slug in MONITORS.items():
        update_group(prefix, slug, existing)
