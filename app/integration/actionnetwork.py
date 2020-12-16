import datetime
import logging

import requests
import sentry_sdk
from django.conf import settings
from django.core.cache import cache
from django.db.models import Exists, OuterRef

from absentee.models import BallotRequest
from common.apm import tracer
from common.enums import ExternalToolType, SubscriberPlan
from multi_tenant.models import Client, SubscriberIntegrationProperty
from register.models import Registration
from reminder.models import ReminderRequest
from smsbot.models import Number
from verifier.models import Lookup

from .models import Link

FORM_ENDPOINT = "https://actionnetwork.org/api/v2/forms/"
ADD_ENDPOINT = "https://actionnetwork.org/api/v2/forms/{form_id}/submissions/"
PEOPLE_ENDPOINT = "https://actionnetwork.org/api/v2/people/{person_id}/"
PERSON_HELPER_ENDPOINT = "https://actionnetwork.org/api/v2/people/"

logger = logging.getLogger("integration")

# ActionNetwork ids (the key) must be lowercase, and match the table name in the
# turnout db.  The form description shows up in the ActionNetwork UI
# and matches the tool name, with title case (value).  See get_form_title().
ACTIONS = {
    "lookup": "Verify",
    "registration": "Register",
    "ballotrequest": "Absentee",
    "reminderrequest": "Reminder",
}

CACHE_KEY = "actionnetwork-forms"


class ActionNetworkError(Exception):
    pass


def get_session(api_key):
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry

    session = requests.Session()
    session.headers["OSDI-API-Token"] = api_key
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(
                total=1,
                backoff_factor=1,
                status_forcelist=[500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "POST", "PUT"],
            )
        ),
    )
    return session


def get_form_title(action_desc, prefix):
    title = f"VoteAmerica {action_desc}"
    if prefix != "prod":
        title += f" ({prefix})"
    return title


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


# parse out form (uu)id *and* action name (for forms created for ACTIONS dict)
def get_form_ids(ids, prefix):
    an_id = None
    va_action = None
    for gid in ids:
        (org, pid) = gid.split(":")
        if org == "action_network":
            an_id = pid
        elif org == "voteamerica" and pid.startswith(prefix + "_"):
            va_action = pid.split("_", 2)[1]
    return an_id, va_action


# parse out form (uu)id for a given form name
def get_form_id(ids, form_name):
    an_id = None
    is_form = False
    for gid in ids:
        (org, pid) = gid.split(":")
        if org == "action_network":
            an_id = pid
        elif org == "voteamerica" and pid == form_name:
            is_form = True
    return an_id if is_form else None


def setup_action_forms(subscriber_id, api_key, slug):
    if subscriber_id:
        key = f"{CACHE_KEY}-{subscriber_id}"
    else:
        key = CACHE_KEY

    forms = cache.get(key) or {}
    missing = False
    for action in ACTIONS.keys():
        if action not in forms:
            missing = True
    if not missing:
        return forms

    session = get_session(api_key)

    logger.info(f"Fetching forms from ActionNetwork for subscriber {subscriber_id}")
    prefix = settings.ACTIONNETWORK_FORM_PREFIX
    forms = {}
    with tracer.trace("an.form", service="actionnetwork"):
        nexturl = FORM_ENDPOINT
        while nexturl:
            logger.info(nexturl)
            response = session.get(nexturl)
            for form in response.json()["_embedded"]["osdi:forms"]:
                an_id, va_action = get_form_ids(form["identifiers"], prefix)
                if an_id and va_action:
                    forms[va_action] = an_id
                    if va_action in ACTIONS:
                        title = get_form_title(ACTIONS[va_action], prefix)
                        if title != form["title"]:
                            logger.info(f"Fixing title for {va_action} form {an_id}")
                            response = session.put(
                                FORM_ENDPOINT + f"/{an_id}", json={"title": title,},
                            )

            nexturl = response.json().get("_links", {}).get("next", {}).get("href")

    for action, tool in ACTIONS.items():
        if action not in forms:
            # This code runs once per action, ever.
            logger.info(f"Creating action form for {tool} ({prefix})")
            with tracer.trace("an.form.create", service="actionnetwork"):
                form_id = f"voteamerica:{prefix}_{action}"
                if subscriber_id and slug:
                    form_id += "_" + slug
                response = session.post(
                    FORM_ENDPOINT,
                    json={
                        "identifiers": [form_id],
                        "title": get_form_title(tool, prefix),
                        "origin_system": "voteamerica",
                    },
                )
                logger.info(response.json())
                an_id, va_action = get_form_ids(response.json()["identifiers"], prefix)
                if an_id and va_action:
                    forms[va_action] = an_id

    cache.set(key, forms, settings.ACTIONNETWORK_FORM_CACHE_TIMEOUT)

    return forms


def post_person(info, form_id, api_key, slug):
    from common.apm import tracer

    session = get_session(api_key)
    url = ADD_ENDPOINT.format(form_id=form_id)
    try:
        with tracer.trace("an.form.submission", service="actionnetwork"):
            response = session.post(url, json=info,)
            if response.status_code != 200:
                extra = {"url": url, "info": info, "status_code": response.status_code}
                logger.info(response.text)
                logger.error(
                    "actionnetwork: Error posting to %(url)s, info %(info)s, status_code %(status_code)s",
                    extra,
                    extra=extra,
                )
                sentry_sdk.capture_exception(
                    ActionNetworkError(
                        f"Error posting to {url}, status code {response.status_code}"
                    )
                )
                return None

            person_id = response.json()["_links"]["osdi:person"]["href"].split("/")[-1]

            # if (first) subscriber field not set, set it
            if slug and not response.json().get("custom_fields", {}).get(
                "first_subscriber"
            ):
                response = session.put(
                    PEOPLE_ENDPOINT.format(person_id=person_id),
                    json={"custom_fields": {"subscriber": slug,},},
                )

    except Exception as e:
        extra = {"url": url, "info": info, "exception": str(e)}
        logger.error(
            "actionnetwork: Error posting to %(url)s, info %(info)s, exception %(exception)s",
            extra,
            extra=extra,
        )
        sentry_sdk.capture_exception(
            ActionNetworkError(f"Error posting to {url}, exception {str(e)}")
        )
        return None

    # return link to the *person*, not the submission
    return person_id


@tracer.wrap()
def sync_item(item):
    if settings.ACTIONNETWORK_SYNC and item.action:
        _sync_item(item, None)
        if item.action.visible_to_subscriber:
            _sync_item(item, item.subscriber_id)


def _sync_item(item, subscriber_id):
    api_key = get_api_key(subscriber_id)
    if not api_key:
        return

    if item.subscriber.default_slug:
        slug = item.subscriber.default_slug.slug
    else:
        slug = None  # this is not good

    forms = setup_action_forms(subscriber_id, api_key, slug)
    action = str(item.__class__.__name__).lower()
    tool = ACTIONS[action]
    form_id = forms.get(action)

    extra = {"subscriber_id": subscriber_id, "item": item}
    logger.info(
        f"actionnetwork: Sync %(item)s, subscriber %(subscriber_id)s",
        extra,
        extra=extra,
    )
    info = {
        "person": {
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
        },
        "action_network:referrer_data": {
            "source": item.source or f"voteamerica_{tool.lower()}",
        },
    }
    if item.phone:
        info["person"]["phone_numbers"] = [{"number": str(item.phone),}]
        if (
            (not subscriber_id or item.sms_opt_in_subscriber)
            and not Number.objects.filter(
                phone=item.phone, opt_out_time__isnull=False
            ).exists()
        ):
            info["person"]["phone_numbers"][0]["status"] = "subscribed"
    if item.embed_url:
        info["action_network:referrer_data"]["website"] = item.embed_url
    if item.email_referrer:
        info["action_network:referrer_data"]["email_referrer"] = item.email_referrer
    if item.mobile_referrer:
        info["action_network:referrer_data"][
            "mobile_message_referrer"
        ] = item.mobile_referrer
    if not subscriber_id:
        info["person"]["custom_fields"] = {"last_subscriber": slug}

    external_id = post_person(
        info, form_id, api_key, slug if not subscriber_id else None,
    )
    if external_id:
        Link.objects.create(
            action_id=item.action_id,
            subscriber_id=subscriber_id,
            external_tool=ExternalToolType.ACTIONNETWORK,
            external_id=external_id,
        )


def sync_all_items(cls):
    from .tasks import sync_action_to_actionnetwork

    pks = set()

    cutoff = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc
    ) - datetime.timedelta(seconds=settings.ACTION_CHECK_UNFINISHED_DELAY)
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
        .filter(no_sync=True, action__isnull=False, created_at__lt=cutoff)
        .order_by("created_at")
    ):
        pks.add(str(item.action_id))

    for item in (
        cls.objects.filter(subscriber__is_first_party=False)
        .annotate(
            no_sync=~Exists(
                Link.objects.filter(
                    subscriber_id=OuterRef("subscriber"),
                    external_tool=ExternalToolType.ACTIONNETWORK,
                    action=OuterRef("action"),
                )
            ),
            has_api_key=Exists(
                SubscriberIntegrationProperty.objects.filter(
                    subscriber_id=OuterRef("subscriber"),
                    external_tool=ExternalToolType.ACTIONNETWORK,
                    name="api_key",
                )
            ),
        )
        .filter(
            no_sync=True, has_api_key=True, action__isnull=False, created_at__lt=cutoff
        )
        .order_by("created_at")
    ):
        pks.add(str(item.action_id))

    logger.info(f"queueing {len(pks)} items to sync to actionnetwork")
    for pk in pks:
        sync_action_to_actionnetwork.delay(pk)


@tracer.wrap()
def sync():
    sync_all_items(Lookup)
    sync_all_items(BallotRequest)
    sync_all_items(Registration)
    sync_all_items(ReminderRequest)


@tracer.wrap()
def sync_subscriber(subscriber: Client) -> None:
    session = get_session(settings.ACTIONNETWORK_SUBSCRIBERS_KEY)
    form_id = get_form(session, "VoteAmerica Tool Users", "subscriber")

    if hasattr(subscriber, "subscription"):
        subscription = subscriber.subscription
    else:
        logger.info(f"No Subscription for subscriber {subscriber}")
        return

    info = {
        "person": {
            "given_name": subscription.primary_contact_first_name,
            "family_name": subscription.primary_contact_last_name,
            "email_addresses": [{"address": subscription.primary_contact_email}],
            "custom_fields": {
                "subscriber_is_c3": subscription.plan == SubscriberPlan.NONPROFIT,
                "subscriber_slug": subscriber.default_slug.slug,
            },
        },
    }
    url = ADD_ENDPOINT.format(form_id=form_id)
    with tracer.trace("an.subscriber_form", service="actionnetwork"):
        response = session.post(url, json=info)

    if response.status_code != 200:
        sentry_sdk.capture_exception(
            ActionNetworkError(
                f"Error posting subscriber to form {url}, status code {response.status_code}"
            )
        )
        logger.warning(
            f"Failed to post subscriber {subscriber} info {info} to actionnetwork: {response.text}"
        )
    logger.info(f"Posted subscriber {subscriber} to actionnetwork")


def get_form(session, form_description: str, form_name: str) -> str:
    if settings.ENV != "prod":
        form_name = f"staging_{form_name}"

    cache_key = f"actionnetwork_form_{form_name}"
    form_id = cache.get(cache_key)
    if form_id:
        return form_id

    nexturl = FORM_ENDPOINT
    while nexturl:
        with tracer.trace("an.form", service="actionnetwork"):
            response = session.get(nexturl,)
        for form in response.json()["_embedded"]["osdi:forms"]:
            an_id = get_form_id(form["identifiers"], form_name)
            if an_id:
                logger.info(f"Found existing {form_name} form {an_id}")
                cache.set(cache_key, an_id)
                return an_id
        nexturl = response.json().get("_links", {}).get("next", {}).get("href")

    raise ActionNetworkError(f"Missing form {form_name}")


def create_form(session, form_description: str, form_name: str) -> str:
    if settings.ENV != "prod":
        form_name = f"staging_{form_name}"
        form_description += " (staging)"

    # create form
    logger.info(f"Creating form {form_name}")
    with tracer.trace("an.form_create", service="actionnetwork"):
        response = session.post(
            FORM_ENDPOINT,
            json={
                "identifiers": [f"voteamerica:{form_name}"],
                "title": form_description,
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
    form_id = get_form_id(response.json()["identifiers"], form_name)
    logger.info(f"Created {form_name} form {form_id}")
    return form_id


@tracer.wrap()
def lookup_person_by_phone(phone: str) -> str:
    last = None
    for cls in BallotRequest, Registration, Lookup, ReminderRequest:
        item = (
            cls.objects.annotate(
                has_an_person=Exists(
                    Link.objects.filter(
                        external_tool=ExternalToolType.ACTIONNETWORK,
                        action=OuterRef("action"),
                    )
                )
            )
            .filter(phone=phone, has_an_person=True,)
            .order_by("-created_at")
            .first()
        )
        if item and (not last or last.created_at < item.created_at):
            last = item

    if last:
        link = Link.objects.filter(
            action=last.action, external_tool=ExternalToolType.ACTIONNETWORK
        ).first()
        if link:
            return link.external_id
    return None


@tracer.wrap()
def unsubscribe_phone(phone):
    # unsubscribe the most recent user of this phone number
    person_id = lookup_person_by_phone(phone)
    if person_id:
        session = get_session(settings.ACTIONNETWORK_KEY)
        with tracer.trace("an.person_update", service="actionnetwork"):
            response = session.put(
                PEOPLE_ENDPOINT.format(person_id=person_id),
                json={
                    "phone_numbers": [{"number": str(phone), "status": "unsubscribed"}]
                },
            )
        logger.info(f"Unsubscribed {phone} from actionnetwork person_id {person_id}")
        return True
    else:
        return False


@tracer.wrap()
def resubscribe_phone(phone):
    # re-subscribe the most recent user of this phone number
    person_id = lookup_person_by_phone(phone)
    if person_id:
        session = get_session(settings.ACTIONNETWORK_KEY)
        with tracer.trace("an.person_update", service="actionnetwork"):
            response = session.put(
                PEOPLE_ENDPOINT.format(person_id=person_id),
                json={
                    "phone_numbers": [{"number": str(phone), "status": "subscribed"}]
                },
            )
        logger.info(f"Resubscribed {phone} to actionnetwork person_id {person_id}")
        return True
    else:
        return False


@tracer.wrap()
def add_test_addrs():
    from common.tasks import TEST_ADDRS

    session = get_session(settings.ACTIONNETWORK_KEY)
    for addr in TEST_ADDRS:
        info = {
            "person": {
                "given_name": "250",
                "family_name": "ok",
                "email_addresses": [{"address": addr}],
            },
            "action_network:referrer_data": {"source": "250ok",},
        }
        response = session.post(PERSON_HELPER_ENDPOINT, json=info,)
