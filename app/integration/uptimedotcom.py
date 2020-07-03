import datetime
import logging
import re

import dateutil.parser
import requests
import tweepy
from django.conf import settings

from common.apm import tracer
from election.models import StateInformation

from .models import ExternalStateSite

logger = logging.getLogger("integration")

MONITORS = {
    "polling-place": "external_tool_polling_place",
    "ovr": "external_tool_ovr",
    "verify-status": "external_tool_verify_status",
    "absentee-application": "external_tool_vbm_application",
    "absentee-tracker": "external_tool_absentee_ballot_tracker",
}
DESCRIPTIONS = {
    "polling-place": "Polling Place Lookup",
    "ovr": "Online Voter Registration",
    "verify-status": "Voter Registration Status Verifier",
    "absentee-application": "Absentee Ballot Request",
    "absentee-tracker": "Absentee Ballot Tracker",
}

CHECKS_ENDPOINT = "https://uptime.com/api/v1/checks/"
ADD_ENDPOINT = "https://uptime.com/api/v1/checks/add-http/"
STATUSPAGES_ENDPOINT = "https://uptime.com/api/v1/statuspages/"

CHECK_FREQUENCY_MINUTES = 10
CHECK_REGIONS = ["US East", "US West", "US Central"]

# as downtime crosses each of these thresholds, we tweet (again)
TWEET_DOWNTIME_THRESHOLDS = [600, 3600, 6 * 3600, 24 * 3600, 7 * 24 * 3600]


class APIError(Exception):
    pass


class APIThrottle(Exception):
    def __init__(self, seconds):
        self.seconds = seconds


@tracer.wrap()
def api_call(verb, url, data=None):
    response = getattr(requests, verb)(
        url, headers={"Authorization": f"Token {settings.UPTIMEDOTCOM_KEY}"}, json=data,
    )
    if response.status_code != 200:
        msg = response.json().get("messages", {})
        if msg.get("error_code") == "API_RATE_LIMIT":
            p = re.compile(r".* (\d+) seconds")
            m = p.match(msg.get("error_message"))
            if m:
                seconds = int(m[1])
                logger.info(f"Throttled by uptime.com; must wait {seconds}")
                raise APIThrottle(seconds)
        raise APIError(response.text)
    return response.json()


def get_existing_checks():
    checks = {}
    nexturl = CHECKS_ENDPOINT
    while nexturl:
        r = api_call("get", nexturl)
        for test in r["results"]:
            checks[test["name"]] = test
        nexturl = r.get("next")
    return checks


def get_existing_pages():
    pages = {}
    r = api_call("get", STATUSPAGES_ENDPOINT)
    for page in r["results"]:
        pages[page["name"]] = page
    return pages


@tracer.wrap()
def update_group(prefix, slug, existing):
    names = []
    for item in StateInformation.objects.filter(field_type__slug=slug):
        # some values are blank
        if not item.text:
            continue

        name = f"{prefix}-{item.state_id}"
        names.append(name)

        site, _ = ExternalStateSite.objects.get_or_create(name=name,)
        desc = f"{item.state_id} {DESCRIPTIONS[prefix]}"
        if site.description != desc or site.state_up is None:
            site.description = desc
            site.state_up = True
            site.save()

        req = {
            "name": name,
            # hack: uptime.com uppercases urlescaped hex, so uppercase our value too to avoid a diff
            "msp_address": item.text.replace("%2f", "%2F"),
            "msp_interval": CHECK_FREQUENCY_MINUTES,
            "contact_groups": ["Default"],
            "locations": CHECK_REGIONS,
        }

        if name in existing:
            old = existing[name]
            del existing[name]

            same = True
            for k, v in req.items():
                if v != old.get(k):
                    logger.info(f"Will change {name} field {k} {old[k]} -> {v}")
                    same = False
            if same:
                continue

            logger.info(f"Updating {name}")
            api_call("patch", f"{CHECKS_ENDPOINT}{old['pk']}/", req)
        else:
            logger.info(f"Adding {name} {item.text}")
            req["type"] = "http"
            api_call("post", ADD_ENDPOINT, req)

    for name, old in existing.items():
        if name.startswith(prefix + "-"):
            logger.info(f"Removing {name}")
            api_call("delete", f"{CHECKS_ENDPOINT}{old['pk']}/")

    return names


@tracer.wrap()
def sync():
    checks = get_existing_checks()
    pages = get_existing_pages()

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
                    logger.info(f"Will change page {prefix} field {k} {old[k]} -> {v}")
                    same = False
            if same:
                continue
            logger.info(f"Updating page {prefix} {page_slug}")
            api_call("patch", f"{STATUSPAGES_ENDPOINT}{pages[prefix]['pk']}/", req)
        else:
            logger.info(f"Creating page {prefix} {page_slug} services {names}")
            api_call("post", f"{STATUSPAGES_ENDPOINT}", req)


def to_pretty_timedelta(n):
    if n < datetime.timedelta(seconds=120):
        return str(int(n.total_seconds())) + "s"
    if n < datetime.timedelta(minutes=120):
        return str(int(n.total_seconds() // 60)) + "m"
    if n < datetime.timedelta(hours=48):
        return str(int(n.total_seconds() // 3600)) + "h"
    if n < datetime.timedelta(days=14):
        return str(int(n.total_seconds() // (24 * 3600))) + "d"
    if n < datetime.timedelta(days=7 * 12):
        return str(int(n.total_seconds() // (24 * 3600 * 7))) + "w"
    if n < datetime.timedelta(days=365 * 2):
        return str(int(n.total_seconds() // (24 * 3600 * 30))) + "M"
    return str(int(n.total_seconds() // (24 * 3600 * 365))) + "y"


@tracer.wrap()
def get_site_uptime(pk):
    now = datetime.datetime.utcnow()
    r = []
    for period, seconds in {
        "week": 7 * 24 * 3600,
        "month": 30 * 24 * 3600,
        "quarter": 91 * 24 * 3600,
        # "year": 365 * 24 * 3600,
    }.items():
        res = api_call(
            "get",
            f"{CHECKS_ENDPOINT}{pk}/stats/?start_date={(now - datetime.timedelta(seconds=seconds)).isoformat()}&end_date={now.isoformat()}",
        )
        down_seconds = res["totals"]["downtime_secs"]
        uptime = res["totals"]["uptime"]
        if down_seconds:
            r.append(
                f"down {to_pretty_timedelta(datetime.timedelta(seconds=down_seconds))} over last {period} ({'%.3f' % (uptime*100)}% uptime)"
            )
    if r:
        return "Overall: " + ", ".join(r)
    return None


def tweet(message):
    auth = tweepy.OAuthHandler(
        settings.UPTIME_TWITTER_CONSUMER_KEY, settings.UPTIME_TWITTER_CONSUMER_SECRET
    )
    auth.set_access_token(
        settings.UPTIME_TWITTER_ACCESS_TOKEN,
        settings.UPTIME_TWITTER_ACCESS_TOKEN_SECRET,
    )

    # Create API object
    api = tweepy.API(auth)

    # Create a tweet
    logger.info(f"Tweet: {message}")
    api.update_status(message)


@tracer.wrap()
def tweet_site_status(site, uptime_state):
    pk = uptime_state["pk"]
    uptime_state["name"]
    message = None
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    if uptime_state["state_is_up"] != site.state_up:
        site.state_up = uptime_state["state_is_up"]
        site.state_changed_at = dateutil.parser.isoparse(
            uptime_state["state_changed_at"]
        )
        if site.state_up:
            message = f"{site.description} is now back up"
        site.save()

    if not site.state_up:
        # complain about being down after crossing several thresholds
        for seconds in TWEET_DOWNTIME_THRESHOLDS:
            cutoff = site.state_changed_at + datetime.timedelta(seconds=seconds)
            if now > cutoff and (not site.last_tweet_at or site.last_tweet_at < cutoff):
                actual_delta = now - site.state_changed_at
                logger.info(
                    f"cutoff {cutoff} {seconds} change at {site.state_changed_at} tweet_at {site.last_tweet_at}"
                )
                message = f"{site.description} has been down for {to_pretty_timedelta(actual_delta)}"
                break

    if message:
        u = get_site_uptime(pk)
        if u:
            message += ". " + u
        message += " " + uptime_state["msp_address"]
        site.last_tweet_at = now
        site.save()
        tweet(message)


@tracer.wrap()
def tweet_all_sites():
    checks = get_existing_checks()
    for site in ExternalStateSite.objects.all():
        if site.name not in checks:
            continue
        tweet_site_status(site, checks[site.name])
