import logging

import requests
import sentry_sdk
from django.conf import settings
from django.db.models import Exists, OuterRef

from absentee.models import BallotRequest
from common.apm import tracer
from common.enums import ExternalToolType
from multi_tenant.models import SubscriberIntegrationProperty
from register.models import Registration
from verifier.models import Lookup

from .models import Link

ADD_ENDPOINT = "https://actionnetwork.org/api/v2/people/"

logger = logging.getLogger("integration")


class ActionNetworkError(Exception):
    pass


def post_person(info, api_key):
    from common.apm import tracer

    with tracer.trace("an.person.add", service="actionnetwork"):
        try:
            response = requests.post(
                ADD_ENDPOINT, json=info, headers={"OSDI-API-Token": api_key},
            )
        except Exception as e:
            extra = {"url": ADD_ENDPOINT, "info": info, "exception": str(e)}
            logger.error(
                "actionnetwork: Error posting to %(url)s, info %(info)s, exception %(exception)s",
                extra,
                extra=extra,
            )
            sentry_sdk.capture_exception(
                ActionNetworkError(
                    f"Error posting to {url}, info {info}, exception {str(e)}"
                )
            )
            return None
    if response.status_code != 200:
        extra = {"url": ADD_ENDPOINT, "info": info, "status_code": response.status_code}
        logger.error(
            "actionnetwork: Error posting to %(url)s, info %(info)s, status_code %(response.status_code)s",
            extra,
            extra=extra,
        )
        sentry_sdk.capture_exception(
            ActionNetworkError(
                f"Error posting to {url}, info {info}, status code {response.status_code}"
            )
        )
        return None

    for ids in response.json().get("identifiers", []):
        if ids.startswith("action_network"):
            return ids.split(":", 1)[1]
    return None


def get_api_key(subscriber_id):
    if subscriber_id:
        api_key = None
        for key in SubscriberIntegrationProperty.objects.filter(
            subscriber_id=subscriber_id,
            external_tool=ExternalToolType.ACTIONNETWORK,
            name="api_key",
        ):
            return key.value
        if not api_key:
            return None
    return settings.ACTIONNETWORK_KEY


@tracer.wrap()
def sync_item(item):
    if settings.ACTIONNETWORK_SYNC and item.action:
        _sync_item(item, None)
        _sync_item(item, item.subscriber_id)


def _sync_item(item, subscriber_id):
    api_key = get_api_key(subscriber_id)
    if not api_key:
        return

    extra = {"subscriber_id": subscriber_id, "item": item}
    logger.info(
        f"actionnetwork: Sync %(item)s, subscriber %(subscriber_id)s",
        extra,
        extra=extra,
    )
    external_id = post_person(
        {
            "given_name": item.first_name,
            "family_name": item.last_name,
            "email_addresses": [{"address": item.email}],
            "postal_addresses": [
                {
                    "address_lines": [item.address1, item.address2],
                    "locality": item.city,
                    "region": item.state_id,
                    "postal_code": item.zipcode,
                    "country": "US",
                },
            ],
            "identifiers": [f"voteamerica_action:{item.action_id.hex_grouped}"],
        },
        api_key,
    )
    if external_id:
        Link.objects.create(
            action_id=item.action_id,
            subscriber_id=subscriber_id,
            external_tool=ExternalToolType.ACTIONNETWORK,
            external_id=external_id,
        )


def sync_all_items(cls):
    for item in (
        cls.objects.annotate(
            no_sync=~Exists(
                Link.objects.filter(
                    subscriber_id=None,
                    external_tool=ExternalToolType.ACTIONNETWORK,
                    action=OuterRef("action"),
                )
            )
        )
        .filter(no_sync=True, action__isnull=False)
        .order_by("created_at")
    ):
        _sync_item(item, None)

    for item in (
        cls.objects.annotate(
            no_sync=~Exists(
                Link.objects.filter(
                    subscriber_id=OuterRef("subscriber"),
                    external_tool=ExternalToolType.ACTIONNETWORK,
                    action=OuterRef("action"),
                )
            )
        )
        .filter(no_sync=True, action__isnull=False)
        .order_by("created_at")
    ):
        _sync_item(item, item.subscriber_id)


@tracer.wrap()
def sync():
    if settings.ACTIONNETWORK_SYNC:
        sync_all_items(Lookup)
        sync_all_items(BallotRequest)
        sync_all_items(Registration)
