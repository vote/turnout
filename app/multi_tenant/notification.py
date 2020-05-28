from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from accounts.models import Invite
from common.analytics import statsd

from .models import Client

NOTIFICATION_TEMPLATE = "multi_tenant/email/new_invite.html"
SUBJECT = "You've been invited to join the VoteAmerica toolset"


@statsd.timed("turnout.multi_tenant.compile_invite_email")
def compile_email(invite: Invite, subscriber: Client) -> str:

    preheader_text = f"Click below to access the {{ subscriber }} subscription"
    recipient = {
        "email": invite.email,
    }
    context = {
        "invite": invite,
        "subscriber": subscriber,
        "recipient": recipient,
        "preheader_text": preheader_text,
    }

    return render_to_string(NOTIFICATION_TEMPLATE, context)


def send_email(invite: Invite, content: str) -> None:
    msg = EmailMessage(
        SUBJECT, content, settings.MANAGEMENT_NOTIFICATION_FROM, [invite.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_notification(invite: Invite, subscriber: Client) -> None:
    content = compile_email(invite, subscriber)
    send_email(invite, content)
