from typing import Tuple

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from common.analytics import statsd

from .contactinfo import get_absentee_contact_info
from .models import AbsenteeLeoEmailOverride, BallotRequest

NOTIFICATION_TEMPLATE = "absentee/email/leo_email.html"

FROM_EMAIL = settings.ABSENTEE_LEO_EMAIL_FROM

OVERRIDE_EMAIL = settings.ABSENTEE_LEO_EMAIL_DISABLE
OVERRIDE_EMAIL_ADDRESS = settings.ABSENTEE_LEO_EMAIL_OVERRIDE_ADDRESS


class NoAbsenteeRequestEmailAddress(Exception):
    pass


def get_leo_email(region_external_id: int) -> str:
    try:
        return AbsenteeLeoEmailOverride.objects.get(pk=region_external_id).email
    except AbsenteeLeoEmailOverride.DoesNotExist:
        pass

    email = get_absentee_contact_info(region_external_id).email
    if not email:
        raise NoAbsenteeRequestEmailAddress()

    return email


@statsd.timed("turnout.absentee.compile_leo_email")
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
        "partner": ballot_request.partner,
        "recipient": recipient,
        "state_info": ballot_request.state.data,
        "preheader_text": None,
        "debug": was_debug_mail,
        "leo_email": real_leo_email,
    }

    return leo_email, render_to_string(NOTIFICATION_TEMPLATE, context)


def send_email(ballot_request: BallotRequest, content: str, leo_email: str) -> None:
    subject = f"Absentee Ballot Application from {ballot_request.first_name} {ballot_request.last_name}"

    msg = EmailMessage(
        subject=subject,
        body=content,
        from_email=FROM_EMAIL,
        to=[leo_email],
        cc=[ballot_request.email],
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
    send_email(ballot_request, content, leo_email)
