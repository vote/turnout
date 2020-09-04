from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.apm import tracer
from common.i90 import shorten_url
from common.rollouts import get_feature_bool
from smsbot.models import Number

from .models import Lookup

UPSELL_TEMPLATE = "verifier/email/external_tool_upsell.html"
UPSELL_SUBJECT = "You've checked your voter registration. Here's what's next."


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


def trigger_upsell(lookup: Lookup) -> None:
    if not get_feature_bool("drip", "verify_external"):
        return

    content = compile_upsell_email(lookup)

    msg = EmailMessage(
        UPSELL_SUBJECT,
        content,
        lookup.subscriber.transactional_from_email_address,
        [lookup.email],
    )
    msg.content_subtype = "html"
    msg.send()

    if lookup.phone:
        try:
            n = Number.objects.get(phone=lookup.phone)
            query_params = lookup.get_query_params()
            reg_link = f"{settings.WWW_ORIGIN}/register-to-vote/?{query_params}"
            vbm_link = f"{settings.WWW_ORIGIN}/vote-by-mail/?{query_params}"
            n.send_sms(
                f"Thanks for checking your registration with VoteAmerica! If you're not registered, we can help you register at {shorten_url(reg_link)}"
            )
            n.send_sms(
                f"If you are already registered, you can request an absentee ballot to vote by mail at {shorten_url(vbm_link)}"
            )
        except ObjectDoesNotExist:
            pass
