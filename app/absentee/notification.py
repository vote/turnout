import logging
from typing import List, Optional

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.apm import tracer
from common.enums import EventType
from common.rollouts import get_feature_bool
from integration.lob import generate_lob_token
from smsbot.models import Number

from .contactinfo import get_absentee_contact_info
from .models import BallotRequest

NOTIFICATION_TEMPLATE = "absentee/email/file_notification.html"
PRINT_AND_FORWARD_NOTIFICATION_TEMPLATE = (
    "absentee/email/print_and_forward_notification.html"
)
EXTERNAL_TOOL_UPSELL_TEMPLATE = "absentee/email/external_tool_upsell.html"

SUBJECT = "ACTION REQUIRED: print and mail your absentee ballot request form."
REMINDER_SUBJECT = "REMINDER: print and mail your absentee ballot request form."
PRINT_AND_FORWARD_SUBJECT = (
    "ACTION REQUIRED: confirm to mail your absentee ballot request form."
)
PRINT_AND_FORWARD_REMINDER_SUBJECT = (
    "REMINDER: confirm to mail your absentee ballot request form."
)
EXTERNAL_TOOL_UPSELL_SUBJECT = (
    "You've requested your absentee ballot. Here's what's next."
)

PRINT_AND_FORWARD_CONFIRM_URL = "{base}/vote-by-mail/confirm/?id={uuid}&token={token}"

logger = logging.getLogger("absentee")


@tracer.wrap()
def compile_email(
    ballot_request: BallotRequest, template: str, preheader: bool = True
) -> str:
    contact_info = get_absentee_contact_info(ballot_request.region.external_id)
    mailing_address = (
        contact_info.full_address
        if contact_info
        else "We were unable to find your local election official mailing address"
    )

    query_params = ballot_request.get_query_params()

    recipient = {
        "first_name": ballot_request.first_name,
        "last_name": ballot_request.last_name,
        "email": ballot_request.email,
    }
    context = {
        "ballot_request": ballot_request,
        "subscriber": ballot_request.subscriber,
        "recipient": recipient,
        "state_info": ballot_request.state.data,
        "mailing_address": mailing_address,
        "query_params": query_params,
    }
    if ballot_request.result_item:
        context["download_url"] = ballot_request.result_item.download_url

    if ballot_request.request_mailing_address1:
        context["mail_download_url"] = ballot_request.result_item_mail.download_url
        context["confirm_url"] = PRINT_AND_FORWARD_CONFIRM_URL.format(
            base=settings.WWW_ORIGIN,
            uuid=ballot_request.action.uuid,
            token=generate_lob_token(ballot_request),
        )
        if preheader:
            context[
                "preheader_text"
            ] = f"{ballot_request.first_name}, click the link below and we'll mail you your form."
    else:
        if preheader:
            context[
                "preheader_text"
            ] = f"{ballot_request.first_name}, just a few more steps to sign-up for an absentee ballot: print, sign and mail your form."
    return render_to_string(template, context)


def send_email(
    ballot_request: BallotRequest,
    subject: str,
    content: str,
    force_to: Optional[str] = None,
) -> None:
    msg = EmailMessage(
        subject,
        content,
        ballot_request.subscriber.transactional_from_email_address,
        [force_to or ballot_request.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_notification(ballot_request: BallotRequest) -> None:
    content = compile_email(
        ballot_request,
        PRINT_AND_FORWARD_NOTIFICATION_TEMPLATE
        if ballot_request.request_mailing_address1
        else NOTIFICATION_TEMPLATE,
    )
    send_email(
        ballot_request,
        PRINT_AND_FORWARD_SUBJECT
        if ballot_request.request_mailing_address1
        else SUBJECT,
        content,
    )


def trigger_reminder(ballot_request: BallotRequest) -> None:
    if ballot_request.request_mailing_address1:
        if not get_feature_bool("drip", "absentee_confirm_reminder"):
            return
    else:
        if not get_feature_bool("drip", "absentee_download_reminder"):
            return

    content = compile_email(
        ballot_request,
        PRINT_AND_FORWARD_NOTIFICATION_TEMPLATE
        if ballot_request.request_mailing_address1
        else NOTIFICATION_TEMPLATE,
    )
    send_email(
        ballot_request,
        PRINT_AND_FORWARD_REMINDER_SUBJECT
        if ballot_request.request_mailing_address1
        else REMINDER_SUBJECT,
        content,
    )

    if ballot_request.phone:
        if ballot_request.request_mailing_address1:
            message = f"Before we will mail your absentee ballot request form, you need to click the confirmation link in the email we sent to {ballot_request.email} from VoteAmerica. We just sent another copy in case you lost it."
        else:
            message = f"We emailed your absentee ballot request form, but you haven't downloaded and printed it yet. We've just resent it to {ballot_request.email} from VoteAmerica."
        try:
            n = Number.objects.get(phone=ballot_request.phone)
            n.send_sms(message)
        except ObjectDoesNotExist:
            pass


@tracer.wrap()
def trigger_print_and_forward_confirm_nag(ballot_request: BallotRequest) -> None:
    if not get_feature_bool("drip", "absentee_unfinished"):
        return

    if ballot_request.phone:
        try:
            n = Number.objects.get(phone=ballot_request.phone)
            n.send_sms(
                f"Before we mail your absentee ballot request form, you need to click the confirmation link in the email we just sent to {ballot_request.email} from VoteAmerica."
            )
        except ObjectDoesNotExist:
            pass


@tracer.wrap()
def trigger_external_tool_upsell(ballot_request: BallotRequest) -> None:
    if not get_feature_bool("drip", "absentee_external"):
        return

    content = compile_email(
        ballot_request, EXTERNAL_TOOL_UPSELL_TEMPLATE, preheader=False
    )
    send_email(ballot_request, EXTERNAL_TOOL_UPSELL_SUBJECT, content)

    tracker_url = ballot_request.state.data.get("external_tool_absentee_ballot_tracker")
    if tracker_url and ballot_request.phone:
        try:
            n = Number.objects.get(phone=ballot_request.phone)
            n.send_sms(
                f"Thank you for requesting your absentee ballot! You can track the progress of your ballot at {tracker_url}"
            )
        except ObjectDoesNotExist:
            pass


def trigger_print_and_forward_notification(ballot_request: BallotRequest) -> None:
    content = compile_email(
        ballot_request, PRINT_AND_FORWARD_NOTIFICATION_TEMPLATE, preheader=False
    )
    send_email(ballot_request, PRINT_AND_FORWARD_SUBJECT, content)


def trigger_test_notifications(recipients: List[str]):
    from event_tracking.models import Event

    # self print
    event = Event.objects.filter(
        event_type=EventType.FINISH_SELF_PRINT, action__ballotrequest__isnull=False
    ).last()
    if not event:
        logger.warning("No ballot requests that finished with self-print")
    else:
        ballot_request = event.action.ballotrequest

        content = compile_email(ballot_request, NOTIFICATION_TEMPLATE)
        for to in recipients:
            send_email(ballot_request, SUBJECT, content, force_to=to)
            send_email(ballot_request, REMINDER_SUBJECT, content, force_to=to)

    # external upsell
    event = Event.objects.filter(
        event_type=EventType.FINISH_EXTERNAL, action__ballotrequest__isnull=False
    ).last()
    if not event:
        logger.warning("No ballot requests that finished with external finish")
    else:
        ballot_request = event.action.ballotrequest

        content = compile_email(
            ballot_request, EXTERNAL_TOOL_UPSELL_TEMPLATE, preheader=False
        )
        for to in recipients:
            send_email(
                ballot_request, EXTERNAL_TOOL_UPSELL_SUBJECT, content, force_to=to
            )

    # print and forward
    event = Event.objects.filter(
        event_type=EventType.FINISH_LOB, action__ballotrequest__isnull=False
    ).last()
    if not event:
        logger.warning("No ballot requests that finished with lob")
    else:
        ballot_request = event.action.ballotrequest

        content = compile_email(
            ballot_request, PRINT_AND_FORWARD_NOTIFICATION_TEMPLATE, preheader=False
        )
        for to in recipients:
            send_email(ballot_request, PRINT_AND_FORWARD_SUBJECT, content, force_to=to)
            send_email(
                ballot_request, PRINT_AND_FORWARD_REMINDER_SUBJECT, content, force_to=to
            )
