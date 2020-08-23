import urllib.parse

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.apm import tracer

from .models import Lookup

UPSELL_TEMPLATE = "verifier/email/external_tool_upsell.html"
UPSELL_SUBJECT = "You've checked your voter registration. Here's what's next."


@tracer.wrap()
def compile_upsell_email(lookup: Lookup) -> str:
    query_param_dict = {
        "first_name": lookup.first_name,
        "last_name": lookup.last_name,
        "address1": lookup.address1,
        "address2": lookup.address2,
        "city": lookup.city,
        "state": lookup.state_id,
        "zipcode": lookup.zipcode,
        "month_of_birth": f"{lookup.date_of_birth.month:02}",
        "day_of_birth": f"{lookup.date_of_birth.day:02}",
        "year_of_birth": f"{lookup.date_of_birth.year}",
        "email": lookup.email,
        "phone": lookup.phone,
        "subscriber": lookup.subscriber.default_slug,
        "utm_campaign": lookup.utm_campaign,
        "utm_source": lookup.utm_source,
        "utm_medium": lookup.utm_medium,
        "utm_term": lookup.utm_term,
        "utm_content": lookup.utm_content,
        "source": lookup.source,
    }

    query_params = urllib.parse.urlencode(
        {k: v for k, v in query_param_dict.items() if v}
    )

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
        "reg_link": f"{settings.VERIFIER_UPSELL_URL}/register-to-vote/?{query_params}",
        "vbm_link": f"{settings.VERIFIER_UPSELL_URL}/vote-by-mail/?{query_params}",
        "state_info": lookup.state.data,
    }

    return render_to_string(UPSELL_TEMPLATE, context)


def trigger_upsell(lookup: Lookup) -> None:
    content = compile_upsell_email(lookup)

    msg = EmailMessage(
        UPSELL_SUBJECT, content, lookup.subscriber.full_email_address, [lookup.email],
    )
    msg.content_subtype = "html"
    msg.send()
