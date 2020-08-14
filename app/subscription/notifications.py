from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

if TYPE_CHECKING:
    from multi_tenant.models import Client

WELCOME_EMAIL_TEMPLATE = "subscription/emails/welcome.html"


def generate_manage_link(view: str, subscriber: "Client") -> str:
    path = reverse(view, args=[subscriber.slug],)
    return f"{settings.PRIMARY_ORIGIN}{path}"


def compile_email(subscriber: "Client", initial_user_email: str) -> str:
    recipient = {"email": initial_user_email}

    context = {
        "custom_embed_code_link": generate_manage_link(
            "manage:multi_tenant:embed_code", subscriber
        ),
        "export_code_link": generate_manage_link(
            "manage:reporting:request", subscriber
        ),
        "user_management_link": generate_manage_link(
            "manage:multi_tenant:manager_list", subscriber
        ),
        "settings_link": generate_manage_link(
            "manage:multi_tenant:settings", subscriber
        ),
        "recipient": recipient,
        "subscriber": subscriber,
    }

    return render_to_string(WELCOME_EMAIL_TEMPLATE, context)


def send_welcome_email(subject: str, initial_user_email: str, content: str) -> None:
    msg = EmailMessage(
        subject, content, settings.MANAGEMENT_NOTIFICATION_FROM, [initial_user_email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_welcome_notification(subscriber: "Client", initial_user_email: str) -> None:
    subject = f"The {subscriber.name} account at VoteAmerica is now active"
    content = compile_email(subscriber, initial_user_email)
    send_welcome_email(subject, initial_user_email, content)
