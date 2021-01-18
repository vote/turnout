import logging
from typing import List

import requests
from django.conf import settings

from common.apm import tracer
from election.models import StateInformation

MONITOR = {
    "external_tool_polling_place": "Polling Place Lookup",
    "external_tool_ovr": "Online Voter Registration",
    "external_tool_verify_status": "Voter Registration Status Verifier",
    "external_tool_vbm_application": "Absentee Ballot Request",
    "external_tool_absentee_ballot_tracker": "Absentee Ballot Tracker",
}

logger = logging.getLogger("integration")


def get_session():
    session = requests.Session()
    session.auth = requests.auth.HTTPBasicAuth(
        settings.UPTIME_USER, settings.UPTIME_SECRET
    )
    return session


def get_random_proxy_str():
    # Borrow a proxy from the uptime bot?
    session = get_session()
    try:
        nexturl = f"{settings.UPTIME_URL}/v1/uptime/proxies/"
        proxies = []
        while nexturl:
            response = session.get(nexturl)
            response.raise_status()
            nexturl = response.json().get("next")
            for proxy in response.json().get("result", []):
                if proxy["status"] == "up":
                    proxies.append(proxy)
        random.shuffle(proxies)
        return f"socks5://{proxy['address']}"

    except:
        return None


def oxford_join(ls: List[str]) -> str:
    if len(ls) <= 2:
        return " and ".join(ls)
    else:
        return ", ".join(ls[0:-1]) + ", and " + ls[-1]


@tracer.wrap()
def config_uptime():
    if not settings.UPTIME_URL.startswith("http"):
        logger.info("No (valid) UPTIME_URL configured")
        return

    sites = {}  # description -> {url, metadata}
    for slug, slug_desc in MONITOR.items():
        for item in StateInformation.objects.filter(field_type__slug=slug):
            # some values are blank
            if not item.text:
                continue

            if item.text in sites:
                sites[item.text]["metadata"]["slug_descs"].append(slug_desc)
                sites[item.text]["metadata"]["slugs"].append(slug)
            else:
                sites[item.text] = {
                    "url": item.text,
                    "metadata": {
                        "state_id": item.state_id,
                        "slugs": [slug],
                        "slug_descs": [slug_desc],
                    },
                }

    # set descriptions
    for url, item in sites.items():
        item[
            "description"
        ] = f"{item['metadata']['state_id']} {oxford_join(item['metadata']['slug_descs'])}"

    # list our existing sites
    session = get_session()

    nexturl = f"{settings.UPTIME_URL}/v1/uptime/sites-mine/"
    while nexturl:
        response = session.get(nexturl)
        response.raise_for_status()
        nexturl = response.json().get("next")

        for item in response.json().get("results", []):
            if item["active"]:
                if item["url"] in sites:
                    want = sites[item["url"]]
                    if (
                        item["description"] != want["description"]
                        or item["metadata"] != want["metadata"]
                    ):
                        logger.info(f"Updating {want}")
                        session.put(
                            f"{settings.UPTIME_URL}/v1/uptime/sites/{item['uuid']}/",
                            json=want,
                        )
                    del sites[item["url"]]
                else:
                    logger.info(
                        f"Disabling {item['description']} {item['url']} {item['uuid']}"
                    )
                    session.put(
                        f"{settings.UPTIME_URL}/v1/uptime/sites/{item['uuid']}/",
                        json={"active": False},
                    )

    # add missing sites
    for desc, item in sites.items():
        logger.info(f"Adding {item}")
        response = session.post(f"{settings.UPTIME_URL}/v1/uptime/sites/", json=item)
        response.raise_for_status()
