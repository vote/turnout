from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.apm import tracer
from integration.lob import generate_lob_token

from .contactinfo import get_registration_contact_info
from .models import Registration

NOTIFICATION_TEMPLATE = "register/email/file_notification.html"
STATE_CONFIRMATION_TEMPLATE = "register/email/state_confirmation.html"
SUBJECT = "ACTION REQUIRED: print and mail your voter registration form."

PRINT_AND_FORWARD_NOTIFICATION_TEMPLATE = (
    "register/email/print_and_forward_notification.html"
)
PRINT_AND_FORWARD_SUBJECT = "ACTION REQUIRED: confirm to mail your registration form."
PRINT_AND_FORWARD_CONFIRM_URL = (
    "{base}/register-to-vote/confirm/?id={uuid}&token={token}"
)


@tracer.wrap()
def compile_email(registration: Registration) -> str:
    contact_info = get_registration_contact_info(registration)

    mailing_address = (
        contact_info.address
        if contact_info
        else "We were unable to find your local election official mailing address"
    )

    preheader_text = f"{registration.first_name}, just a few more steps to complete your voter registration: print, sign and mail your form."
    recipient = {
        "first_name": registration.first_name,
        "last_name": registration.last_name,
        "email": registration.email,
    }
    context = {
        "registration": registration,
        "subscriber": registration.subscriber,
        "recipient": recipient,
        "download_url": registration.result_item.download_url,
        "mailing_address": mailing_address,
        "state_info": registration.state.data,
        "preheader_text": preheader_text,
    }

    return render_to_string(NOTIFICATION_TEMPLATE, context)


def send_email(registration: Registration, subject, content: str) -> None:
    msg = EmailMessage(
        subject,
        content,
        registration.subscriber.full_email_address,
        [registration.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_notification(registration: Registration) -> None:
    content = compile_email(registration)
    send_email(registration, SUBJECT, content)


def trigger_state_confirmation(registration: Registration) -> None:
    content = render_to_string(
        NOTIFICATION_TEMPLATE,
        {
            "registration": registration,
            "subscriber": registration.subscriber,
            "recipient": {
                "first_name": registration.first_name,
                "last_name": registration.last_name,
                "email": registration.email,
            },
            "state_info": registration.state.data,
        },
    )
    send_email(registration, SUBJECT, content)


def trigger_print_and_forward_notification(registration: Registration) -> None:
    content = render_to_string(
        PRINT_AND_FORWARD_NOTIFICATION_TEMPLATE,
        {
            "registration": registration,
            "subscriber": registration.subscriber,
            "recipient": {
                "first_name": registration.first_name,
                "last_name": registration.last_name,
                "email": registration.email,
            },
            "download_url": registration.result_item.download_url,
            "state_info": registration.state.data,
            "mail_download_url": registration.result_item_mail.download_url,
            "confirm_url": PRINT_AND_FORWARD_CONFIRM_URL.format(
                base=settings.WWW_ORIGIN,
                uuid=registration.action.uuid,
                token=generate_lob_token(registration),
            ),
        },
    )
    send_email(registration, PRINT_AND_FORWARD_SUBJECT, content)
