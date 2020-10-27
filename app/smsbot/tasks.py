import datetime
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from common.analytics import statsd
from common.rollouts import get_feature_bool

from .models import Blast, Number

logger = logging.getLogger("smsbot")


@statsd.timed("turnout.smsbot.tasks._send_welcome_sms")
def _send_welcome_sms(number: str, origin: str = None) -> Number:
    if not number:
        return None

    n, _ = Number.objects.get_or_create(phone=number)

    if n.opt_in_time:
        # The user has already opted-in.  Do nothing.
        return n

    # If Twilio's Advanced opt-in is enabled: If the user has
    #  opted-out (STOP), they won't receive this message.  If they
    #  also sent UNSTOP or JOIN but not YES, they may receive this
    #  message, but our record will still have an opt_out_time since
    #  they didn't full opt back in.

    now = timezone.now()
    if n.welcome_time and (
        settings.SMS_OPTIN_REMINDER_RESEND_SECONDS is None
        or n.welcome_time
        + datetime.timedelta(seconds=settings.SMS_OPTIN_REMINDER_RESEND_SECONDS)
        > now
    ):
        return n

    phrase = {
        "register": "registering to vote via",
        "absentee": "requesting a ballot via",
        "verifier": "checking your registration via",
    }.get(origin, "signing up with")
    msg = f"Thanks for {phrase} VoteAmerica. We send 2-4 txts a month with election info. Msg & Data rates may apply. Text STOP to unsubscribe."

    n.welcome_time = now
    n.save()

    n.send_sms(msg)
    return n


@shared_task(queue="high-pri")
def send_welcome_sms(number: str, origin: str = None) -> None:
    _send_welcome_sms(number, origin)


@shared_task
def poll_twilio() -> None:
    from .poll import poll

    if get_feature_bool("smsbot", "poll"):
        poll()


@shared_task(queue="blast-sms")
def trigger_blast_sms(number_id: str, blast_id: str) -> None:
    from .blast import send_blast_sms

    number = Number.objects.get(pk=number_id)
    blast = Blast.objects.get(pk=blast_id)
    send_blast_sms(number, blast)


@shared_task(queue="blast-mms")
def trigger_voter_map_mms(voter_id: str, blast_id: str, destination: str) -> None:
    from voter.models import Voter
    from .blast import send_voter_map_mms

    voter = Voter.objects.get(uuid=voter_id)
    blast = Blast.objects.get(uuid=blast_id)
    send_voter_map_mms(voter, blast, destination)
