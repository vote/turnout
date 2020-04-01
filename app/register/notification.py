from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.analytics import statsd

from .models import Registration

NOTIFICATION_TEMPLATE = "register/email/file_notification.html"
SUBJECT = "Here's your voter registration form!"


@statsd.timed("turnout.register.compile_email")
def compile_email(registration: Registration) -> str:
    preheader_text = f"{registration.first_name}, we've generated a personalized document for you to send to election officials. You must submit this document to be registered for future elections."
    recipient = {
        "first_name": registration.first_name,
        "last_name": registration.last_name,
        "email": registration.email,
    }
    context = {
        "registration": registration,
        "partner": registration.partner,
        "recipient": recipient,
        "download_url": registration.result_item.download_url,
        "state_info": registration.state.data,
        "preheader_text": preheader_text,
    }

    return render_to_string(NOTIFICATION_TEMPLATE, context)


def send_email(registration: Registration, content: str) -> None:
    msg = EmailMessage(
        SUBJECT, content, registration.partner.full_email_address, [registration.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_notification(registration: Registration) -> None:
    content = compile_email(registration)
    send_email(registration, content)
