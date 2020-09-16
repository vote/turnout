import datetime
import logging
import time

import requests
import sentry_sdk
from django.conf import settings

from common.apm import tracer

from .actionnetwork import ActionNetworkError
from .actionnetwork import get_session as get_actionnetwork_session
from .models import MymoveLead

STAGING_LEADS_ENDPOINT = "https://staging-leads.mymove.com/v2/clients/{client_id}/leads"
PROD_LEADS_ENDPOINT = "https://leads.mymove.com/v2/clients/{client_id}/leads"

ACTIONNETWORK_FORM_ENDPOINT = "https://actionnetwork.org/api/v2/forms/"
ACTIONNETWORK_ADD_ENDPOINT = (
    "https://actionnetwork.org/api/v2/forms/{form_id}/submissions/"
)

logger = logging.getLogger("integration")


class MymoveError(Exception):
    pass


@tracer.wrap()
def pull(days: int = None, hours: int = None) -> None:
    if settings.ENV == "prod":
        url = PROD_LEADS_ENDPOINT
    else:
        url = STAGING_LEADS_ENDPOINT

    if not days and not hours:
        # include an extra hour|day so we don't miss any records
        hours = settings.MYMOVE_PULL_INTERVAL_HOURS + 1
    if hours:
        url += f"?hrs={hours}"
    elif days:
        url += f"?days={days}"
    url = url.format(client_id=settings.MYMOVE_ID)

    with tracer.trace("mymove.leads", service="mymove"):
        response = requests.get(
            url,
            headers={
                "Authorization": settings.MYMOVE_SECRET,
                "Content-Type": "application/json",
            },
        )
    if response.status_code != 200:
        logger.error(
            f"Mymove endpoint {url} returned {response.status_code}: {response.text}"
        )
        sentry_sdk.capture_exception(
            MymoveError(f"Mymove endpoint {url} return {response.status_code}")
        )
        return

    leads = response.json()["leads"]
    logger.info(f"Fetched {len(leads)} leads")
    store_leads(leads)


def load_leads_from_file(fn):
    import json

    with open(fn, "r") as f:
        j = f.read()
        leads = json.loads(j)["leads"]
        logger.info(f"Loaded {len(leads)} leads from {fn}")
        store_leads(leads)


def load_leads_from_csv(fn, n=0, d=1):
    import csv

    with open(fn, "r") as f:
        r = csv.DictReader(f, delimiter=",")
        leads = [i for i in r]
        chunk = len(leads) // d
        logger.info(f"Loaded {len(leads)} leads from {fn}, chunk {chunk} ({n} of {d})")
        store_leads(leads[(n * chunk) : ((n + 1) * chunk)])


def store_leads(leads):
    new = 0
    for lead in leads:
        # avoid duplicates
        try:
            created_at = datetime.datetime.strptime(
                lead["created_at"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=datetime.timezone.utc)
            move_date = datetime.datetime.strptime(
                lead["move_date"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=datetime.timezone.utc)
        except:
            # csv has different date format :/
            created_at = datetime.datetime.strptime(
                lead["created_at"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=datetime.timezone.utc)
            move_date = datetime.datetime.strptime(
                lead["move_date"], "%Y-%m-%d"
            ).replace(tzinfo=datetime.timezone.utc)
        lead, created = MymoveLead.objects.get_or_create(
            email=lead.get("email"),
            mymove_created_at=created_at,
            defaults={
                "mymove_created_at": created_at,
                "email": lead.get("email"),
                "first_name": lead.get("first_name"),
                "last_name": lead.get("last_name"),
                "move_date": move_date,
                "new_address1": lead.get("new_address_1"),
                "new_address2": lead.get("new_address_2"),
                "new_city": lead.get("new_city"),
                "new_state": lead.get("new_state"),
                "new_zipcode": lead.get("new_postal_code"),
                "new_zipcode_plus4": lead.get("new_postal_code_plus4"),
                "new_housing_tenure": lead.get("new_housing_tenure"),
                "old_address1": lead.get("old_address_1"),
                "old_address2": lead.get("old_address_2"),
                "old_city": lead.get("old_city"),
                "old_state": lead.get("old_state"),
                "old_zipcode": lead.get("old_postal_code"),
                "old_zipcode_plus4": lead.get("old_postal_code_plus4"),
                "old_housing_tenure": lead.get("old_housing_tenure"),
            },
        )
        if created:
            new += 1

    logger.info(f"Imported {new} new leads, skipped {len(leads) - new} dups")


@tracer.wrap()
def get_or_create_form(session: requests.Session) -> str:
    logger.info(f"Fetching forms from ActionNetwork")

    if settings.ENV != "prod":
        form_name = "staging_mymove_lead"
    else:
        form_name = "prod_mymove_lead"

    def get_form_id(ids):
        an_id = None
        is_form = False
        for gid in ids:
            (org, pid) = gid.split(":")
            if org == "action_network":
                an_id = pid
            elif org == "voteamerica" and pid == form_name:
                is_form = True
        return an_id if is_form else None

    nexturl = ACTIONNETWORK_FORM_ENDPOINT
    while nexturl:
        with tracer.trace("an.form", service="actionnetwork"):
            response = session.get(nexturl,)
        for form in response.json()["_embedded"]["osdi:forms"]:
            an_id = get_form_id(form["identifiers"])
            if an_id:
                logger.info(f"Found existing {form_name} form {an_id}")
                return an_id
        nexturl = response.json().get("_links", {}).get("next", {}).get("href")

    # create form
    logger.info(f"Creating form {form_name}")
    title = f"VoteAmerica MyMove lead"
    if settings.ENV != "prod":
        title += f" ({settings.ENV})"
    with tracer.trace("an.form_create", service="actionnetwork"):
        response = session.post(
            ACTIONNETWORK_FORM_ENDPOINT,
            json={
                "identifiers": [f"voteamerica:{form_name}"],
                "title": title,
                "origin_system": "voteamerica",
            },
        )
    if response.status_code != 200:
        logger.error(
            f"Failed to create ActionNetwork {form_name} form: {response.status_code} {response.text}"
        )
        raise ActionNetworkError(
            f"Failed to create {form_name} form, status_code {response.status_code}"
        )
    form_id = get_form_id(response.json()["identifiers"])
    logger.info(f"Created {form_name} form {form_id}")
    return form_id


@tracer.wrap()
def push_lead(session: requests.Session, form_id: str, lead: MymoveLead) -> None:
    info = {
        "person": {
            "given_name": lead.first_name,
            "family_name": lead.last_name,
            "email_addresses": [{"address": lead.email}],
            "postal_addresses": [
                {
                    "address_lines": [lead.new_address1, lead.new_address2 or ""],
                    "locality": lead.new_city,
                    "region": lead.new_state,
                    "postal_code": lead.new_zipcode,
                    "country": "US",
                },
            ],
            "custom_fields": {
                "subscriber": "mymove",
                # store new address here too, in case of competing contact info updates
                "mymove_new_address": " ".join(
                    [lead.new_address1, lead.new_address2 or ""]
                ),
                "mymove_new_city": lead.new_city,
                "mymove_new_state": lead.new_state,
                "mymove_new_zipcode": lead.new_zipcode,
                "mymove_new_housing_tenure": lead.new_housing_tenure,
                "mymove_old_address": " ".join(
                    [lead.old_address1, lead.old_address2 or ""]
                ),
                "mymove_old_city": lead.old_city,
                "mymove_old_state": lead.old_state,
                "mymove_old_zipcode": lead.old_zipcode,
                "mymove_old_housing_tenure": lead.old_housing_tenure,
                "mymove_move_date": lead.move_date.isoformat(),
                "mymove_cross_state": lead.old_state != lead.new_state,
            },
        },
        "action_network:referrer_data": {"source": "mymove",},
    }
    url = ACTIONNETWORK_ADD_ENDPOINT.format(form_id=form_id)
    with tracer.trace("an.mymove_form", service="actionnetwork"):
        response = session.post(url, json=info,)

    if response.status_code != 200:
        sentry_sdk.capture_exception(
            ActionNetworkError(
                f"Error posting mymove lead to form {url}, status code {response.status_code}"
            )
        )
        logger.error(
            f"Failed to post {lead} info {info} to actionnetwork: {response.text}"
        )
    else:
        person_id = response.json()["_links"]["osdi:person"]["href"].split("/")[-1]
        logger.info(f"Synced {lead} to actionnetwork person {person_id}")
        lead.actionnetwork_person_id = person_id
        lead.save()


@tracer.wrap()
def push_to_actionnetwork(limit=None, offset=0, new_state=None) -> None:
    session = get_actionnetwork_session(settings.ACTIONNETWORK_KEY)

    form_id = get_or_create_form(session)

    q = MymoveLead.objects.filter(
        actionnetwork_person_id__isnull=True,
        mymove_created_at__gte=datetime.datetime(
            2020, 9, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        ),
    ).order_by("mymove_created_at")
    if new_state:
        q = q.filter(new_state=new_state)

    if limit:
        end = offset + limit
    else:
        end = None

    for lead in q[offset:end]:
        push_lead(session, form_id, lead)
        time.sleep(settings.ACTIONNETWORK_SYNC_DELAY)
