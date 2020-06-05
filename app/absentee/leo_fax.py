from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.analytics import statsd
from fax.send_fax import send_fax

from .contactinfo import AbsenteeContactInfo, get_absentee_contact_info
from .models import BallotRequest
from .tasks import send_ballotrequest_leo_fax_sent_notification

NOTIFICATION_TEMPLATE_SUBMITTED = "absentee/email/leo_fax_submitted.html"
NOTIFICATION_TEMPLATE_SENT = "absentee/email/leo_fax_sent.html"

REPLY_TO = settings.ABSENTEE_LEO_FAX_EMAIL_REPLY_TO


class NoAbsenteeRequestFaxAddress(Exception):
    pass


@statsd.timed("turnout.absentee.compile_email")
def compile_email(
    ballot_request: BallotRequest,
    leo_contact: AbsenteeContactInfo,
    notification_template: str,
) -> str:
    recipient = {
        "first_name": ballot_request.first_name,
        "last_name": ballot_request.last_name,
        "email": ballot_request.email,
    }

    context = {
        "ballot_request": ballot_request,
        "subscriber": ballot_request.subscriber,
        "recipient": recipient,
        "state_info": ballot_request.state.data,
        "preheader_text": None,
        "leo_contact": leo_contact,
        "has_leo_contact": bool(
            leo_contact and (leo_contact.email or leo_contact.phone)
        ),
        "download_url": ballot_request.result_item.download_url,
    }

    return render_to_string(notification_template, context)


def send_fax_submitted_email(
    ballot_request: BallotRequest, leo_contact: AbsenteeContactInfo
) -> None:
    subject = f"Your absentee ballot application is being sent"

    msg = EmailMessage(
        subject=subject,
        body=compile_email(
            ballot_request, leo_contact, NOTIFICATION_TEMPLATE_SUBMITTED
        ),
        from_email=ballot_request.subscriber.full_email_address,
        to=[ballot_request.email],
        reply_to=[REPLY_TO],
    )

    msg.content_subtype = "html"
    msg.send()


def send_fax_and_fax_submitted_email(ballot_request: BallotRequest) -> None:
    leo_contact = get_absentee_contact_info(ballot_request.region.external_id)

    if not leo_contact.fax:
        raise NoAbsenteeRequestFaxAddress()

    send_fax(
        ballot_request.result_item,
        leo_contact.fax,
        send_ballotrequest_leo_fax_sent_notification.name,
        ballot_request.uuid,
    )
    send_fax_submitted_email(ballot_request, leo_contact)


def send_fax_sent_email(ballot_request: BallotRequest) -> None:
    leo_contact = get_absentee_contact_info(ballot_request.region.external_id)
    subject = f"Re: Your absentee ballot application is being sent"

    msg = EmailMessage(
        subject=subject,
        body=compile_email(ballot_request, leo_contact, NOTIFICATION_TEMPLATE_SENT),
        from_email=ballot_request.subscriber.full_email_address,
        to=[ballot_request.email],
        reply_to=[REPLY_TO],
    )

    msg.content_subtype = "html"
    msg.send()
