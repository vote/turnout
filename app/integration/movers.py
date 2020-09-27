import datetime
import logging
import re
import time

import requests
import sentry_sdk
from django.conf import settings
from django.core.cache import cache
from django.db.models import F
from django.forms.models import model_to_dict
from django.template.defaultfilters import slugify
from pdf_template import PDFTemplate, PDFTemplateSection

from action.models import Action
from common import enums
from common.apm import tracer
from common.pdf.pdftemplate import fill_pdf_template
from common.rollouts import get_feature_bool, get_feature_int
from election.models import State, StateInformation
from event_tracking.models import Event
from multi_tenant.models import Client
from official.api_views import get_regions_for_address
from register.contactinfo import get_nvrf_submission_address
from register.generateform import (
    BLANK_FORMS_COVER_SHEET_8PT_PATH,
    BLANK_FORMS_COVER_SHEET_9PT_PATH,
    BLANK_FORMS_COVER_SHEET_PATH,
    PRINT_AND_FORWARD_TEMPLATE_PATH,
)
from storage.models import StorageItem

from .actionnetwork import ActionNetworkError
from .actionnetwork import get_session as get_actionnetwork_session
from .lob import get_or_create_lob_address, submit_lob
from .models import MoverLead

ACTIONNETWORK_FORM_ENDPOINT = "https://actionnetwork.org/api/v2/forms/"
ACTIONNETWORK_ADD_ENDPOINT = (
    "https://actionnetwork.org/api/v2/forms/{form_id}/submissions/"
)

RE_MARKUP_LINK = re.compile(
    "\[({0})]\(\s*({1})\s*\)".format(
        "[^]]+",  # Anything that isn't a square closing bracket
        "http[s]?://[^)]+",  # http:// or https:// followed by anything but a closing paren
    )
)


logger = logging.getLogger("integration")


class MoverError(Exception):
    pass


def get_mover_subscriber() -> Client:
    return Client.objects.filter(default_slug__slug=settings.MOVER_SOURCE).first()


@tracer.wrap()
def pull(days: int = None, hours: int = None) -> None:
    url = settings.MOVER_LEADS_ENDPOINT

    if not days and not hours:
        # include an extra hour|day so we don't miss any records
        hours = settings.MOVER_PULL_INTERVAL_HOURS + 1
    if hours:
        url += f"?hrs={hours}"
    elif days:
        url += f"?days={days}"
    url = url.format(client_id=settings.MOVER_ID)

    with tracer.trace("mover.leads", service="mover"):
        response = requests.get(
            url,
            headers={
                "Authorization": settings.MOVER_SECRET,
                "Content-Type": "application/json",
            },
        )
    if response.status_code != 200:
        logger.error(
            f"Mover endpoint {url} returned {response.status_code}: {response.text}"
        )
        sentry_sdk.capture_exception(
            MoverError(f"Mover endpoint {url} return {response.status_code}")
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
        lead, created = MoverLead.objects.get_or_create(
            email=lead.get("email"),
            source_created_at=created_at,
            defaults={
                "source_created_at": created_at,
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
def send_blank_register_forms_tx(offset=0, limit=None) -> None:
    from .tasks import send_blank_register_forms_to_lead as send_forms_task

    q = MoverLead.objects.filter(
        new_state="TX",
        created_at__gte=datetime.datetime(2020, 9, 16, 0, 0, 0).replace(
            tzinfo=datetime.timezone.utc
        ),
        blank_register_forms_action__isnull=True,
        new_housing_tenure="rent",
    )
    end = None
    if limit:
        end = offset + limit
    queue_async = get_feature_bool("movers", "blank_forms_tx_async")
    max_minutes = get_feature_int("movers", "blank_forms_tx_max_minutes") or 55
    logger.info(
        f"send_blank_register_forms_tx offset={offset}, limit={limit}, count={q.count()}, "
        f"async={queue_async}, max_minutes={max_minutes}"
    )
    for lead in q[offset:end]:
        if queue_async:
            send_forms_task.apply_async(args=(lead.uuid,), expire=(max_minutes * 60))
        else:
            send_blank_register_forms_to_lead(lead)


@tracer.wrap()
def send_blank_register_forms_blankforms2020(offset=0, limit=None, state=None) -> None:
    # experimental data set (exclude control group!)
    states = [
        "AZ",
        "GA",
        "FL",
        "MI",
        "NC",
        "PA",
        "WI",
        "OH",
        "MN",
        "CO",
        "IA",
        "ME",
        "NE",
        "KS",
        "SC",
        "AL",
        "MS",
        "MT",
        "UT",
    ]
    if state:
        states = [state]
    q = (
        MoverLead.objects.filter(
            new_state__in=states,
            created_at__lt=datetime.datetime(
                2020, 9, 16, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
            blank_register_forms_action__isnull=True,
            actionnetwork_person_id__isnull=True,
        )
        .exclude(new_state=F("old_state"))
        .exclude(uuid__startswith="0")
        .exclude(uuid__startswith="1")
    )
    end = None
    if limit:
        end = offset + limit
    print(f"states {states} offset {offset} limit {limit} count {q.count()}")
    for lead in q[offset:end]:
        send_blank_register_forms_to_lead(lead)


def send_blank_register_forms(offset=0, limit=None, state=None) -> None:
    from .tasks import send_blank_register_forms_to_lead as send_forms_task

    # post-experiment, moving forward
    states = [
        "AZ",
        "GA",
        "FL",
        "MI",
        "NC",
        "PA",
        "WI",
        "OH",
        "MN",
        "CO",
        "IA",
        "ME",
        "NE",
        "KS",
        "SC",
        "AL",
        "MS",
        "MT",
        "UT",
    ]
    if state:
        states = [state]
    q = MoverLead.objects.filter(
        new_state__in=states,
        created_at__gte=datetime.datetime(
            2020, 9, 16, 0, 0, 0, tzinfo=datetime.timezone.utc
        ),
        blank_register_forms_action__isnull=True,
        new_housing_tenure="rent",
    ).exclude(new_state=F("old_state"))
    if limit:
        offset + limit
    queue_async = get_feature_bool("movers", "blank_forms_tx_async")
    max_minutes = get_feature_int("movers", "blank_forms_tx_max_minutes") or 55
    logger.info(
        f"send_blank_register_forms states {states}, offset={offset}, limit={limit}, count={q.count()}, async={queue_async}, max_minutes={max_minutes}"
    )
    for lead in q[0:limit]:
        if queue_async:
            send_forms_task.apply_async(args=(lead.uuid,), expire=(max_minutes * 60))
        else:
            send_blank_register_forms_to_lead(lead)


def get_register_form_data(lead: MoverLead):
    form_data = model_to_dict(lead)
    contact_info = get_nvrf_submission_address(lead.new_region_id, lead.new_state)
    mailto_address = contact_info.address

    # split by linebreaks, because each line is a separate field in the PDF
    for num, line in enumerate(mailto_address.splitlines()):
        form_data[f"mailto_line_{num+1}"] = line
        form_data[f"mailto_line_upper_{num+1}"] = line.upper()

    state = State.objects.get(code=lead.new_state)
    form_data["new_state_name"] = state.name

    # grab all (new_)state fields
    for info in StateInformation.objects.select_related("field_type").filter(
        state=state,
    ):
        v = info.text.replace("**Warning:**", "WARNING:")
        v = v.replace("**", "")  # remove other emphasis
        v = v.replace("*", "\u2022")
        if lead.new_state in ["AL"]:
            # get stingy
            v = v.replace("\n\n", "\n")
        form_data[info.field_type.slug] = RE_MARKUP_LINK.sub(r"\1", v)

    form_data["registration_nvrf_combined"] = "\n".join(
        [
            "Box 6 (ID Number):",
            "  " + form_data["registration_nvrf_box_6"],
            "",
            "Box 7 (Choice of Party):",
            "  " + form_data["registration_nvrf_box_7"],
            "",
            "Box 8 (Race or Ethnic Group):",
            "  " + form_data["registration_nvrf_box_8"],
        ]
    )

    # 2020 dates
    def cap_first_letter(s):
        return s[0].upper() + s[1:]

    dates = [
        f"Deadline to register: {cap_first_letter(form_data['2020_registration_deadline_by_mail'])}",
    ]
    if (
        form_data["2020_early_voting_starts"]
        and form_data["2020_early_voting_starts"] != "N/A"
    ):
        dates.extend(
            [
                f"Early voting starts: {form_data['2020_early_voting_starts']}",
                f"Early voting ends: {form_data['2020_early_voting_ends']}",
            ]
        )
    dates.append(f"Election day: November 3, 2020")
    form_data["important_dates"] = "\n".join(dates)
    form_data["2020_state_deadline"] = form_data["2020_registration_deadline_by_mail"]

    if lead.new_state == "WI":
        form_data[
            "registration_rules"
        ] += "\n\n\u2022\u2022 WARNING \u2022\u2022 You must also provide Proof of Residence documentation that shows your name and current residential address. Acceptable forms include: a copy of your current and valid WI Driver's License or State ID card; any other official ID card or license issued by a WI governmental body or unit; any ID card issued by an employer with a photo of the card holder, but not including a business card; a real estate tax bill or receipt for the current year or the year preceding the date of the election; a university, college or technical college ID card (must include photo) ONLY if the voter provides a fee receipt dated within the last 9 months or the institution provides a certified housing list to the municipal clerk; a gas, electric or phone utility bill for the period commencing no earlier than 90 days before Election Day; a bank or credit card statement; a paycheck or paystub; a check or other document issued by a unit of government; an intake document from a residential care facility such as a nursing home."

    return form_data


@tracer.wrap()
def send_blank_register_forms_to_lead(lead: MoverLead) -> None:
    # make sure we've geocoded
    if not lead.new_region:
        geocode_lead(lead)

    subscriber = get_mover_subscriber()

    if not lead.blank_register_forms_item:
        # generate PDF
        form_data = get_register_form_data(lead)
        item = StorageItem(
            app=enums.FileType.BLANK_REGISTRATION_FORMS,
            email=lead.email,
            subscriber=subscriber,
        )
        filename = (
            slugify(f"{lead.new_state} {lead.last_name} blank-register-forms").lower()
            + ".pdf"
        )
        if lead.new_state in ["AL", "WI"]:
            cover_path = BLANK_FORMS_COVER_SHEET_8PT_PATH
        elif lead.new_state in ["MI", "FL"]:
            cover_path = BLANK_FORMS_COVER_SHEET_9PT_PATH
        else:
            cover_path = BLANK_FORMS_COVER_SHEET_PATH
        fill_pdf_template(
            PDFTemplate(
                [
                    PDFTemplateSection(
                        path=cover_path, is_form=True, flatten_form=True
                    ),
                    PDFTemplateSection(
                        path=PRINT_AND_FORWARD_TEMPLATE_PATH,
                        is_form=False,
                        flatten_form=False,
                    ),
                    PDFTemplateSection(
                        path=PRINT_AND_FORWARD_TEMPLATE_PATH,
                        is_form=False,
                        flatten_form=False,
                    ),
                ]
            ),
            form_data,
            item,
            filename,
        )
        lead.blank_register_forms_item = item
    else:
        logger.info(f"Already generated PDF for {lead}")

    if not lead.blank_register_forms_action:
        lead.blank_register_forms_action = Action.objects.create()
    else:
        logger.info(f"Already have blank forms action for {lead}")

    lead.save()

    if Event.objects.filter(
        action=lead.blank_register_forms_action,
        event_type=enums.EventType.LOB_SENT_BLANK_REGISTER_FORMS,
    ).exists():
        logger.info(f"Already submitted lob letter for {lead}")
    else:
        # send
        to_addr = get_or_create_lob_address(
            str(lead.uuid),
            f"{lead.first_name} {lead.last_name}".title(),
            lead.new_address1,
            lead.new_address2,
            lead.new_city,
            lead.new_state,
            lead.new_zipcode,
        )

        created_at = submit_lob(
            f"Blank register, {lead}",
            lead.blank_register_forms_action,
            to_addr,
            lead.blank_register_forms_item.file,
            subscriber,
            double_sided=False,
        )

        lead.blank_register_forms_action.track_event(
            enums.EventType.LOB_SENT_BLANK_REGISTER_FORMS
        )


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


@tracer.wrap()
def get_or_create_form(session: requests.Session) -> str:
    logger.info(f"Fetching forms from ActionNetwork")

    form_name = f"{settings.ENV}_{settings.MOVER_SOURCE}_lead"

    cache_key = f"actionnetwork_form_{form_name}"
    form_id = cache.get(cache_key)
    if form_id:
        return form_id

    nexturl = ACTIONNETWORK_FORM_ENDPOINT
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


@tracer.wrap()
def create_form(session: requests.Session):
    form_name = f"{settings.ENV}_{settings.MOVER_SOURCE}_lead"

    # create form
    logger.info(f"Creating form {form_name}")
    title = f"VoteAmerica {settings.MOVER_SOURCE} lead"
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
    form_id = get_form_id(response.json()["identifiers"], form_name)
    logger.info(f"Created {form_name} form {form_id}")
    return form_id


@tracer.wrap()
def push_lead(lead: MoverLead) -> None:
    session = get_actionnetwork_session(settings.ACTIONNETWORK_KEY)
    form_id = get_or_create_form(session)
    _push_lead(session, form_id, lead)


@tracer.wrap()
def _push_lead(session: requests.Session, form_id: str, lead: MoverLead) -> None:
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
                f"{settings.MOVER_SOURCE}_new_address": " ".join(
                    [lead.new_address1, lead.new_address2 or ""]
                ),
                f"{settings.MOVER_SOURCE}_new_city": lead.new_city,
                f"{settings.MOVER_SOURCE}_new_state": lead.new_state,
                f"{settings.MOVER_SOURCE}_new_zipcode": lead.new_zipcode,
                f"{settings.MOVER_SOURCE}_new_housing_tenure": lead.new_housing_tenure,
                f"{settings.MOVER_SOURCE}_old_address": " ".join(
                    [lead.old_address1, lead.old_address2 or ""]
                ),
                f"{settings.MOVER_SOURCE}_old_city": lead.old_city,
                f"{settings.MOVER_SOURCE}_old_state": lead.old_state,
                f"{settings.MOVER_SOURCE}_old_zipcode": lead.old_zipcode,
                f"{settings.MOVER_SOURCE}_old_housing_tenure": lead.old_housing_tenure,
                f"{settings.MOVER_SOURCE}_move_date": lead.move_date.isoformat(),
                f"{settings.MOVER_SOURCE}_cross_state": lead.old_state
                != lead.new_state,
                f"{settings.MOVER_SOURCE}_cross_region": lead.old_region_id
                != lead.new_region_id,
            },
        },
    }
    url = ACTIONNETWORK_ADD_ENDPOINT.format(form_id=form_id)
    with tracer.trace("an.mover_form", service="actionnetwork"):
        response = session.post(url, json=info,)

    if response.status_code != 200:
        sentry_sdk.capture_exception(
            ActionNetworkError(
                f"Error posting mover lead to form {url}, status code {response.status_code}"
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
    from .tasks import push_mover_to_actionnetwork

    session = get_actionnetwork_session(settings.ACTIONNETWORK_KEY)

    form_id = get_or_create_form(session)

    q = MoverLead.objects.filter(
        actionnetwork_person_id__isnull=True,
        source_created_at__gte=datetime.datetime(
            2020, 9, 16, 0, 0, 0, tzinfo=datetime.timezone.utc
        ),
    ).order_by("source_created_at")
    if new_state:
        q = q.filter(new_state=new_state)

    if limit:
        end = offset + limit
    else:
        end = None

    queue_async = get_feature_bool("movers", "push_to_actionnetwork_async")
    max_minutes = get_feature_int("movers", "push_to_actionnetwork_max_minutes") or 55

    for lead in q[offset:end]:
        if queue_async:
            push_mover_to_actionnetwork.apply_async(
                args=(lead.pk,), expire=(max_minutes * 60)
            )
        else:
            _push_lead(session, form_id, lead)
            time.sleep(settings.ACTIONNETWORK_SYNC_DELAY)


def geocode_lead(lead: MoverLead) -> None:
    updated = False
    new_regions, _ = get_regions_for_address(
        lead.new_address1, lead.new_city, lead.new_state, lead.new_zipcode
    )
    if new_regions and len(new_regions) == 1:
        lead.new_region = new_regions[0]
        updated = True
    old_regions, _ = get_regions_for_address(
        lead.old_address1, lead.old_city, lead.old_state, lead.old_zipcode
    )
    if old_regions and len(old_regions) == 1:
        lead.old_region = old_regions[0]
        updated = True
    if updated:
        lead.save()
        logger.info(
            f"Geocoded {lead}: {lead.old_state} {lead.old_region_id} -> {lead.new_state} {lead.new_region_id}"
        )


def geocode_leads(
    new_state: str = None, old_state: str = None, limit: int = None
) -> None:
    from .tasks import geocode_mover

    q = MoverLead.objects.filter(new_region_id__isnull=True, old_region_id__isnull=True)
    if new_state:
        q = q.filter(new_state=new_state)
    if old_state:
        q = q.filter(old_state=old_state)

    queue_async = get_feature_bool("movers", "geocode_async")
    max_minutes = get_feature_int("movers", "geocode_max_minutes") or 55
    for lead in q[0:limit]:
        if queue_async:
            geocode_mover.apply_async(args=(str(lead.uuid),), expire=(max_minutes * 60))
        else:
            geocode_lead(lead)
