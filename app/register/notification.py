from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.apm import tracer
from common.i90 import shorten_url
from common.rollouts import get_feature_bool
from integration.lob import generate_lob_token
from smsbot.models import Number

from .contactinfo import get_registration_contact_info
from .models import Registration

NOTIFICATION_TEMPLATE = "register/email/file_notification.html"
STATE_CONFIRMATION_TEMPLATE = "register/email/state_confirmation.html"
PRINT_AND_FORWARD_NOTIFICATION_TEMPLATE = (
    "register/email/print_and_forward_notification.html"
)
PRINT_AND_FORWARD_MAILED_TEMPLATE = "register/email/print_and_forward_mailed.html"
PRINT_AND_FORWARD_RETURNED_TEMPLATE = "register/email/print_and_forward_returned.html"
MAIL_CHASE_TEMPLATE = "register/email/mail_chase.html"
EXTERNAL_TOOL_UPSELL_TEMPLATE = "register/email/external_tool_upsell.html"

SUBJECT = "ACTION REQUIRED: print and mail your voter registration form."
REMINDER_SUBJECT = "REMINDER: print and mail your voter registration form."
PRINT_AND_FORWARD_SUBJECT = "ACTION REQUIRED: confirm to mail your registration form."
PRINT_AND_FORWARD_REMINDER_SUBJECT = "REMINDER: confirm to mail your registration form."
PRINT_AND_FORWARD_MAILED_SUBJECT = "Your voter registration form should arrive soon!"
PRINT_AND_FORWARD_RETURNED_SUBJECT = (
    "WARNING: Your voter registration form was not delivered!"
)
MAIL_CHASE_SUBJECT = "Check your voter registration"
EXTERNAL_TOOL_SUBJECT = "You've registered to vote. Here's what's next."

PRINT_AND_FORWARD_CONFIRM_URL = (
    "{base}/register-to-vote/confirm/?id={uuid}&token={token}"
)


@tracer.wrap()
def compile_email(
    registration: Registration, template: str, preheader: bool = True
) -> str:
    contact_info = get_registration_contact_info(registration)

    mailing_address = (
        contact_info.address
        if contact_info
        else "We were unable to find your local election official mailing address"
    )

    recipient = {
        "first_name": registration.first_name,
        "last_name": registration.last_name,
        "email": registration.email,
    }
    query_params = registration.get_query_params()
    context = {
        "registration": registration,
        "subscriber": registration.subscriber,
        "recipient": recipient,
        "download_url": registration.result_item.download_url,
        "mailing_address": mailing_address,
        "state_info": registration.state.data,
        "query_params": query_params,
        "vbm_link": f"{settings.WWW_ORIGIN}/vote-by-mail/?{query_params}",
    }

    if registration.request_mailing_address1:
        context["mail_download_url"] = registration.result_item_mail.download_url
        context["confirm_url"] = PRINT_AND_FORWARD_CONFIRM_URL.format(
            base=settings.WWW_ORIGIN,
            uuid=registration.action.uuid,
            token=generate_lob_token(registration),
        )
        if preheader:
            context[
                "preheader_text"
            ] = f"{registration.first_name}, click the link below and we'll mail you for registration form."
    else:
        if preheader:
            context[
                "preheader_text"
            ] = f"{registration.first_name}, just a few more steps to complete your voter registration: print, sign and mail your form."

    return render_to_string(template, context)


def send_email(registration: Registration, subject, content: str) -> None:
    msg = EmailMessage(
        subject,
        content,
        registration.subscriber.transactional_from_email_address,
        [registration.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_notification(registration: Registration) -> None:
    content = compile_email(
        registration,
        PRINT_AND_FORWARD_NOTIFICATION_TEMPLATE
        if registration.request_mailing_address1
        else NOTIFICATION_TEMPLATE,
    )
    send_email(
        registration,
        PRINT_AND_FORWARD_SUBJECT if registration.request_mailing_address1 else SUBJECT,
        content,
    )


def trigger_reminder(registration: Registration) -> None:
    if registration.request_mailing_address1:
        if not get_feature_bool("drip", "register_confirm_reminder"):
            return
    else:
        if not get_feature_bool("drip", "register_download_reminder"):
            return

    content = compile_email(
        registration,
        PRINT_AND_FORWARD_NOTIFICATION_TEMPLATE
        if registration.request_mailing_address1
        else NOTIFICATION_TEMPLATE,
    )
    send_email(
        registration,
        PRINT_AND_FORWARD_REMINDER_SUBJECT
        if registration.request_mailing_address1
        else REMINDER_SUBJECT,
        content,
    )

    if registration.phone:
        if registration.request_mailing_address1:
            message = f"Before we mail your registration form, you need to click the confirmation link in the email we sent to {registration.email} from VoteAmerica. We just sent another copy in case you lost it."
        else:
            message = f"We emailed your voter registration form, but you haven't downloaded and printed it yet. We've just resent it to {registration.email} from VoteAmerica."
        try:
            n = Number.objects.get(phone=registration.phone)
            n.send_sms(message)
        except ObjectDoesNotExist:
            pass


def trigger_state_confirmation(registration: Registration) -> None:
    content = compile_email(registration, NOTIFICATION_TEMPLATE)
    send_email(registration, SUBJECT, content)


@tracer.wrap()
def trigger_print_and_forward_confirm_nag(registration: Registration) -> None:
    if not get_feature_bool("drip", "register_unfinished"):
        return

    if registration.phone:
        try:
            n = Number.objects.get(phone=registration.phone)
            n.send_sms(
                f"Before we mail your registration form, you need to click the confirmation link in the email we just sent to {registration.email} from VoteAmerica."
            )
        except ObjectDoesNotExist:
            pass


@tracer.wrap()
def trigger_external_tool_upsell(registration: Registration) -> None:
    if not get_feature_bool("drip", "register_external"):
        return

    content = compile_email(
        registration, EXTERNAL_TOOL_UPSELL_TEMPLATE, preheader=False
    )
    send_email(registration, EXTERNAL_TOOL_SUBJECT, content)

    if registration.phone:
        query_params = registration.get_query_params()
        vbm_link = f"{settings.WWW_ORIGIN}/vote-by-mail/?{query_params}"
        try:
            n = Number.objects.get(phone=registration.phone)
            n.send_sms(
                f"Thank you for registering to vote! We can also help you request an absentee ballot to vote by mail at {shorten_url(vbm_link)}"
            )
        except ObjectDoesNotExist:
            pass


@tracer.wrap()
def trigger_print_and_forward_mailed(registration: Registration) -> None:
    if not get_feature_bool("drip", "register_lob_mailed"):
        return

    content = compile_email(
        registration, PRINT_AND_FORWARD_MAILED_TEMPLATE, preheader=False
    )
    send_email(registration, PRINT_AND_FORWARD_MAILED_SUBJECT, content)

    if registration.phone:
        try:
            n = Number.objects.get(phone=registration.phone)
            n.send_sms(
                f"Your registration form should be delivered in the next 24 hours. Be sure to sign and mail it soon! -VoteAmerica"
            )
        except ObjectDoesNotExist:
            pass


@tracer.wrap()
def trigger_print_and_forward_returned(registration: Registration) -> None:
    if not get_feature_bool("drip", "register_lob_returned"):
        return

    content = compile_email(
        registration, PRINT_AND_FORWARD_RETURNED_TEMPLATE, preheader=False
    )
    send_email(registration, PRINT_AND_FORWARD_RETURNED_SUBJECT, content)

    if registration.phone:
        try:
            n = Number.objects.get(phone=registration.phone)
            n.send_sms(
                f"Unfortunately, the registration form that we mailed to you has been returned to us by the postal service. Please try to register again and double-check the mailing address! -VoteAmerica"
            )
        except ObjectDoesNotExist:
            pass


@tracer.wrap()
def trigger_mail_chase(registration: Registration) -> None:
    if not get_feature_bool("drip", "register_mail_chase"):
        return

    content = compile_email(registration, MAIL_CHASE_TEMPLATE, preheader=False)
    send_email(registration, MAIL_CHASE_SUBJECT, content)
