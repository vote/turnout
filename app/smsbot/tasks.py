import datetime

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from common.analytics import statsd


@shared_task
@statsd.timed("turnout.smsbot.tasks.send_welcome_sms")
def send_welcome_sms(number: str, origin: str = None) -> None:
    from .models import Number

    n, _ = Number.objects.get_or_create(phone=number)

    if n.opt_in_time:
        # The user has already opted-in.  Do nothing.
        return

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
        return

    phrase = {
        "register": "registering to vote via",
        "absentee": "requesting a ballot via",
        "verifier": "checking your registration via",
    }.get(origin, "signing up with")
    msg = f"Thanks for {phrase} VoteAmerica. We send 2-4 txts a month with election info. Msg & Data rates may apply. Text STOP to unsubscribe."

    n.welcome_time = now
    n.save()

    n.send_sms(msg)


@shared_task
@statsd.timed("turnout.smsbot.tasks.send_reminder_sms")
def send_reminder_sms(number: str) -> None:
    from .models import Number

    n = Number.objects.get(phone=number)
    if not n:
        # We have no record of this user--do not send them a reminder.
        return

    if n.opt_out_time:
        # If the user has (really) opted out, do not send them anything.  Note
        # that Twilio's advanced opt-in may also prevent us from sending something
        # even if we tried.  It is also possible they opted-out, and then sent
        # UNSTOP or JOIN but not YES so that they can receive our message but we
        # still show them as opted out.  Either way, we should not contact them.
        return

    msg = (
        "Reminder: You are subscribed to VoteAmerica Election Alerts. "
        "Msg & Data rates may apply. 4 msgs/month. "
        "Reply HELP for help, STOP to cancel."
    )

    n.send_sms(msg)
