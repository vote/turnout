from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.analytics import statsd

from .contactinfo import get_absentee_contact_info
from .models import BallotRequest

NOTIFICATION_TEMPLATE = "absentee/email/file_notification.html"
SUBJECT = "ACTION REQUIRED: print and mail your absentee ballot request form."


@statsd.timed("turnout.absentee.compile_email")
def compile_email(ballot_request: BallotRequest) -> str:
    contact_info = get_absentee_contact_info(ballot_request.region.external_id)

    preheader_text = f"{ballot_request.first_name}, just a few more steps to complete your absentee ballot request: print, sign and mail your form."
    recipient = {
        "first_name": ballot_request.first_name,
        "last_name": ballot_request.last_name,
        "email": ballot_request.email,
    }
    context = {
        "ballot_request": ballot_request,
        "partner": ballot_request.partner,
        "recipient": recipient,
        "download_url": ballot_request.result_item.download_url,
        "state_info": ballot_request.state.data,
        "preheader_text": preheader_text,
        "mailing_address": contact_info.mailing_address,
    }

    return render_to_string(NOTIFICATION_TEMPLATE, context)


def send_email(ballot_request: BallotRequest, content: str) -> None:
    msg = EmailMessage(
        SUBJECT,
        content,
        ballot_request.partner.full_email_address,
        [ballot_request.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_notification(ballot_request: BallotRequest) -> None:
    content = compile_email(ballot_request)
    send_email(ballot_request, content)
