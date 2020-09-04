import datetime
import logging

import requests
import sentry_sdk
from django.conf import settings

from common.apm import tracer

from .actionnetwork import ActionNetworkError
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

    new = 0
    for lead in leads:
        # avoid duplicates
        created_at = datetime.datetime.strptime(
            lead["created_at"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=datetime.timezone.utc)
        lead, created = MymoveLead.objects.get_or_create(
            email=lead.get("email"),
            mymove_created_at=created_at,
            defaults={
                "mymove_created_at": created_at,
                "email": lead.get("email"),
                "first_name": lead.get("first_name"),
                "last_name": lead.get("last_name"),
                "move_date": datetime.datetime.strptime(
                    lead["move_date"], "%Y-%m-%dT%H:%M:%SZ"
                ).replace(tzinfo=datetime.timezone.utc),
                "new_address1": lead.get("new_address_1"),
                "new_address2": lead.get("new_address_2"),
                "new_city": lead.get("new_city"),
                "new_state_id": lead.get("new_state"),
                "new_zipcode": lead.get("new_postal_code"),
                "new_zipcode_plus4": lead.get("new_postal_code_plus4"),
                "new_housing_tenure": lead.get("new_housing_tenure"),
                "old_address1": lead.get("old_address_1"),
                "old_address2": lead.get("old_address_2"),
                "old_city": lead.get("old_city"),
                "old_state_id": lead.get("old_state"),
                "old_zipcode": lead.get("old_postal_code"),
                "old_zipcode_plus4": lead.get("old_postal_code_plus4"),
                "old_housing_tenure": lead.get("old_housing_tenure"),
            },
        )
        if created:
            new += 1

    logger.info(f"Imported {new} new leads, skipped {len(leads) - new} dups")


@tracer.wrap()
def get_or_create_form() -> str:
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
            response = requests.get(
                nexturl, headers={"OSDI-API-Token": settings.ACTIONNETWORK_KEY},
            )
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
        response = requests.post(
            ACTIONNETWORK_FORM_ENDPOINT,
            headers={"OSDI-API-Token": settings.ACTIONNETWORK_KEY},
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
def push_lead(form_id: str, lead: MymoveLead) -> None:
    info = {
        "person": {
            "given_name": lead.first_name,
            "family_name": lead.last_name,
            "email_addresses": [{"address": lead.email}],
            "postal_addresses": [
                {
                    "address_lines": [lead.new_address1, lead.new_address2 or ""],
                    "locality": lead.new_city,
                    "region": lead.new_state_id,
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
                "mymove_new_state": lead.new_state_id,
                "mymove_new_zipcode": lead.new_zipcode,
                "mymove_new_housing_tenure": lead.new_housing_tenure,
                "mymove_old_address": " ".join(
                    [lead.old_address1, lead.old_address2 or ""]
                ),
                "mymove_old_city": lead.old_city,
                "mymove_old_state": lead.old_state_id,
                "mymove_old_zipcode": lead.old_zipcode,
                "mymove_old_housing_tenure": lead.old_housing_tenure,
                "mymove_move_date": lead.move_date.isoformat(),
                "mymove_cross_state": lead.old_state_id != lead.new_state_id,
            },
        },
        "action_network:referrer_data": {"source": "mymove",},
    }
    url = ACTIONNETWORK_ADD_ENDPOINT.format(form_id=form_id)
    with tracer.trace("an.mymove_form", service="actionnetwork"):
        response = requests.post(
            url, json=info, headers={"OSDI-API-Token": settings.ACTIONNETWORK_KEY,},
        )

    if response.status_code != 200:
        sentry_sdk.capture_exception(
            ActionNetworkError(
                "Error posting mymove lead to form {url}, status code {response.status_code}"
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
def push_to_actionnetwork(limit=None) -> None:
    form_id = get_or_create_form()

    num = 0
    for lead in MymoveLead.objects.filter(actionnetwork_person_id__isnull=True):
        push_lead(form_id, lead)
        num += 1
        if limit and num >= limit:
            break
