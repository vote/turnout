import logging
from typing import List, Optional

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.apm import tracer
from common.enums import EventType
from fax.send_fax import send_fax

from .contactinfo import AbsenteeContactInfo, get_absentee_contact_info
from .models import BallotRequest
from .tasks import send_ballotrequest_leo_fax_sent_notification

NOTIFICATION_TEMPLATE_SUBMITTED = "absentee/email/leo_fax_submitted.html"
NOTIFICATION_TEMPLATE_SENT = "absentee/email/leo_fax_sent.html"

REPLY_TO = settings.ABSENTEE_LEO_FAX_EMAIL_REPLY_TO

logger = logging.getLogger("absentee")


class NoAbsenteeRequestFaxAddress(Exception):
    pass


@tracer.wrap()
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
    ballot_request: BallotRequest,
    leo_contact: AbsenteeContactInfo,
    force_to: Optional[str] = None,
) -> None:
    subject = f"Your absentee ballot application is being sent"

    msg = EmailMessage(
        subject=subject,
        body=compile_email(
            ballot_request, leo_contact, NOTIFICATION_TEMPLATE_SUBMITTED
        ),
        from_email=ballot_request.subscriber.transactional_from_email_address,
        to=[force_to or ballot_request.email],
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


def send_fax_sent_email(
    ballot_request: BallotRequest, force_to: Optional[str] = None
) -> None:
    leo_contact = get_absentee_contact_info(ballot_request.region.external_id)
    subject = f"Re: Your absentee ballot application is being sent"

    msg = EmailMessage(
        subject=subject,
        body=compile_email(ballot_request, leo_contact, NOTIFICATION_TEMPLATE_SENT),
        from_email=ballot_request.subscriber.transactional_from_email_address,
        to=[force_to or ballot_request.email],
        reply_to=[REPLY_TO],
    )

    msg.content_subtype = "html"
    msg.send()


def trigger_test_fax_emails(recipients: List[str]) -> None:
    from event_tracking.models import Event

    event = Event.objects.filter(
        event_type=EventType.FINISH_LEO, action__ballotrequest__isnull=False
    ).last()
    if not event:
        logger.warning("No ballot requests that finished with a LEO fax")
    else:
        ballot_request = event.action.ballotrequest
        leo_contact = get_absentee_contact_info(ballot_request.region.external_id)
        for to in recipients:
            send_fax_submitted_email(ballot_request, leo_contact, force_to=to)
            send_fax_sent_email(ballot_request, force_to=to)
