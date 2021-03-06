from typing import List, Optional

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from accounts.models import Invite
from common.apm import tracer

from .models import Client

NOTIFICATION_TEMPLATE = "multi_tenant/email/new_invite.html"
SUBJECT = "You have been added to a VoteAmerica subscriber team"


@tracer.wrap()
def compile_email(invite: Invite, subscriber: Client) -> str:

    recipient = {
        "email": invite.email,
    }
    context = {
        "invite": invite,
        "subscriber": subscriber,
        "recipient": recipient,
    }

    return render_to_string(NOTIFICATION_TEMPLATE, context)


def send_email(invite: Invite, content: str, force_to: Optional[str] = None) -> None:
    msg = EmailMessage(
        SUBJECT,
        content,
        settings.MANAGEMENT_NOTIFICATION_FROM,
        [force_to or invite.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_notification(invite: Invite, subscriber: Client) -> None:
    content = compile_email(invite, subscriber)
    send_email(invite, content)


def trigger_test_notifications(recipients: List[str]) -> None:
    invite = Invite.objects.last()
    subscriber = Client.objects.last()

    content = compile_email(invite, subscriber)
    for to in recipients:
        send_email(invite, content, force_to=to)
