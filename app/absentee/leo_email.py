import email.utils
import logging
from typing import List, Tuple

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from common.apm import tracer
from common.enums import EventType

from .contactinfo import get_absentee_contact_info
from .models import BallotRequest

NOTIFICATION_TEMPLATE = "absentee/email/leo_email.html"

FROM_EMAIL = settings.ABSENTEE_LEO_EMAIL_FROM

OVERRIDE_EMAIL = settings.ABSENTEE_LEO_EMAIL_DISABLE
OVERRIDE_EMAIL_ADDRESS = settings.ABSENTEE_LEO_EMAIL_OVERRIDE_ADDRESS

logger = logging.getLogger("absentee")


class NoAbsenteeRequestEmailAddress(Exception):
    pass


def get_leo_email(region_external_id: int) -> str:
    email = get_absentee_contact_info(region_external_id).email
    if not email:
        raise NoAbsenteeRequestEmailAddress()

    return email


@tracer.wrap()
def compile_email(ballot_request: BallotRequest) -> Tuple[str, str]:
    real_leo_email = get_leo_email(ballot_request.region.external_id)

    leo_email = real_leo_email
    was_debug_mail = False
    if OVERRIDE_EMAIL:
        leo_email = OVERRIDE_EMAIL_ADDRESS
        was_debug_mail = True

    recipient = {
        "email": ballot_request.email,
    }

    context = {
        "ballot_request": ballot_request,
        "subscriber": ballot_request.subscriber,
        "recipient": recipient,
        "state_info": ballot_request.state.data,
        "preheader_text": None,
        "debug": was_debug_mail,
        "leo_email": real_leo_email,
    }

    return leo_email, render_to_string(NOTIFICATION_TEMPLATE, context)


def send_email(
    ballot_request: BallotRequest, content: str, leo_email: str, cc_email: str
) -> None:
    subject = f"Absentee Ballot Application from {ballot_request.first_name} {ballot_request.last_name}"

    msg = EmailMessage(
        subject=subject,
        body=content,
        from_email=f'"{email.utils.quote(ballot_request.first_name)} {email.utils.quote(ballot_request.last_name)}" <{FROM_EMAIL}>',
        to=[leo_email],
        cc=[cc_email],
        reply_to=[FROM_EMAIL, leo_email, ballot_request.email],
    )

    attachment = ballot_request.result_item.file
    with attachment.open() as f:
        basename = slugify(
            f"ballot request {ballot_request.last_name} {ballot_request.first_name}"
        )

        msg.attach(
            f"{basename}.pdf", f.read(), "application/pdf",
        )

    msg.content_subtype = "html"
    msg.send()


def trigger_leo_email(ballot_request: BallotRequest) -> None:
    leo_email, content = compile_email(ballot_request)
    send_email(ballot_request, content, leo_email, ballot_request.email)


def trigger_test_leo_email(recipients: List[str]) -> None:
    from event_tracking.models import Event

    event = Event.objects.filter(
        event_type=EventType.FINISH_LEO, action__ballotrequest__isnull=False
    ).last()
    if not event:
        logger.warning("No ballot requests that finished with a LEO email")
    else:
        ballot_request = event.action.ballotrequest
        leo_email, content = compile_email(ballot_request)
        for to in recipients:
            send_email(ballot_request, content, to, to)
