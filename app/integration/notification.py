import logging
from typing import List, Optional

from django.core.mail import EmailMessage
from django.forms.models import model_to_dict
from django.template.loader import render_to_string

from common.apm import tracer
from election.models import State
from register.contactinfo import get_nvrf_submission_address

from .models import MymoveLead

BLANK_FORMS_MAILED_TEMPLATE = "email/blank_forms_mailed.html"
BLANK_FORMS_CHASE_TEMPLATE = "email/blank_forms_chase.html"

BLANK_FORMS_MAILED_SUBJECT = "Your voter registration forms should arrive today"
BLANK_FORMS_REMINDER_SUBJECT = "Don't forget to mail your voter registration form"
BLANK_FORMS_CHASE_SUBJECT = "Time to check your voter registration"


logger = logging.getLogger("integration")


@tracer.wrap()
def compile_email(lead: MymoveLead, template: str, reminder: bool = None) -> str:
    contact_info = get_nvrf_submission_address(lead.new_region_id, lead.new_state)
    mailing_address = (
        contact_info.address
        if contact_info
        else "We were unable to find your local election official mailing address"
    )
    state = State.objects.filter(code=lead.new_state).first()
    context = {
        "lead": model_to_dict(lead),
        "mailing_address": mailing_address,
        "state_full": state.name if state else None,
        "state_info": state.data if state else {},
        "reminder": reminder,
    }

    if contact_info and (contact_info.email or contact_info.phone):
        contact_info_lines = []
        if contact_info.email:
            contact_info_lines.append(f"Email: {contact_info.email}")
        if contact_info.phone:
            contact_info_lines.append(f"Phone: {contact_info.phone}")

        context["leo_contact_info"] = "\n".join(contact_info_lines)
    else:
        context[
            "leo_contact_info"
        ] = "https://www.voteamerica.com/local-election-offices/"
    return render_to_string(template, context)


def send_email(
    lead: MymoveLead, subject, content: str, force_to: Optional[str] = None
) -> None:
    msg = EmailMessage(
        subject,
        content,
        "VoteAmerica <hello@voteamerica.com>",
        [force_to or lead.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_blank_forms_mailed(lead: MymoveLead) -> None:
    content = compile_email(lead, BLANK_FORMS_MAILED_TEMPLATE, False)
    send_email(lead, BLANK_FORMS_MAILED_SUBJECT, content)


def trigger_blank_forms_reminder(lead: MymoveLead) -> None:
    content = compile_email(lead, BLANK_FORMS_MAILED_TEMPLATE, True)
    send_email(lead, BLANK_FORMS_REMINDER_SUBJECT, content)


def trigger_blank_forms_chase(lead: MymoveLead) -> None:
    content = compile_email(lead, BLANK_FORMS_CHASE_TEMPLATE)
    send_email(lead, BLANK_FORMS_CHASE_SUBJECT, content)


def trigger_test_notifications(recipients: List[str]) -> None:
    lead = MymoveLead.objects.filter(blank_register_forms_action__isnull=False).last()
    if not lead:
        logger.warning("No MymoveLead blank form emails")
    else:
        content1 = compile_email(lead, BLANK_FORMS_MAILED_TEMPLATE, False)
        content2 = compile_email(lead, BLANK_FORMS_MAILED_TEMPLATE, True)
        content3 = compile_email(lead, BLANK_FORMS_CHASE_TEMPLATE)

        for to in recipients:
            send_email(lead, BLANK_FORMS_MAILED_SUBJECT, content1, force_to=to)
            send_email(lead, BLANK_FORMS_REMINDER_SUBJECT, content2, force_to=to)
            send_email(lead, BLANK_FORMS_CHASE_SUBJECT, content3, force_to=to)
