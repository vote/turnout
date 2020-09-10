import logging
from typing import List, Optional

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.apm import tracer
from common.enums import EventType
from common.i90 import shorten_url
from common.rollouts import get_feature_bool
from smsbot.models import Number

from .models import Lookup

UPSELL_TEMPLATE = "verifier/email/external_tool_upsell.html"
UPSELL_SUBJECT = "You've checked your voter registration. Here's what's next."


logger = logging.getLogger("verifier")


@tracer.wrap()
def compile_upsell_email(lookup: Lookup) -> str:
    query_params = lookup.get_query_params()
    preheader_text = f"{lookup.first_name}, here's what to do next"
    recipient = {
        "first_name": lookup.first_name,
        "last_name": lookup.last_name,
        "email": lookup.email,
    }
    context = {
        "lookup": lookup,
        "subscriber": lookup.subscriber,
        "recipient": recipient,
        "preheader_text": preheader_text,
        "reg_link": f"{settings.WWW_ORIGIN}/register-to-vote/?{query_params}",
        "vbm_link": f"{settings.WWW_ORIGIN}/vote-by-mail/?{query_params}",
        "state_info": lookup.state.data,
    }

    return render_to_string(UPSELL_TEMPLATE, context)


def send_email(lookup, content, subject, force_to: Optional[str] = None) -> None:
    msg = EmailMessage(
        subject,
        content,
        lookup.subscriber.transactional_from_email_address,
        [force_to or lookup.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_upsell(lookup: Lookup) -> None:
    if not get_feature_bool("drip", "verify_external"):
        return

    content = compile_upsell_email(lookup)
    send_email(lookup, content, UPSELL_SUBJECT)

    if lookup.phone:
        try:
            n = Number.objects.get(phone=lookup.phone)
            if lookup.subscriber.is_first_party:
                query_params = lookup.get_query_params()
                reg_link = f"{settings.WWW_ORIGIN}/register-to-vote/?{query_params}"
                vbm_link = f"{settings.WWW_ORIGIN}/vote-by-mail/?{query_params}"
            else:
                reg_link = f"{settings.WWW_ORIGIN}/register-to-vote/"
                vbm_link = f"{settings.WWW_ORIGIN}/vote-by-mail/"
            n.send_sms(
                f"Thanks for checking your registration with VoteAmerica! If you are not registered to vote, we can help you register at {shorten_url(reg_link)}"
            )
            n.send_sms(
                f"If you are already registered, you can request an absentee ballot to vote by mail at {shorten_url(vbm_link)}"
            )
        except ObjectDoesNotExist:
            pass


def trigger_test_notifications(recipients: List[str]) -> None:
    from event_tracking.models import Event

    event = Event.objects.filter(
        event_type=EventType.FINISH_EXTERNAL, action__lookup__isnull=False
    ).last()
    if not event:
        logger.warning("No lookups that finished with external")
    else:
        lookup = event.action.lookup
        content = compile_upsell_email(lookup)
        for to in recipients:
            send_email(lookup, content, UPSELL_SUBJECT, force_to=to)
