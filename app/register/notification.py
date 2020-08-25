from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.apm import tracer

from .contactinfo import get_registration_contact_info
from .models import Registration

NOTIFICATION_TEMPLATE = "register/email/file_notification.html"
STATE_CONFIRMATION_TEMPLATE = "register/email/state_confirmation.html"
SUBJECT = "ACTION REQUIRED (CORRECTED): print and mail your voter registration form."


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


def send_email(registration: Registration, content: str) -> None:
    msg = EmailMessage(
        SUBJECT,
        content,
        registration.subscriber.full_email_address,
        [registration.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_notification(registration: Registration) -> None:
    content = compile_email(registration)
    send_email(registration, content)


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
    send_email(registration, content)
