from celery import shared_task
from django.conf import settings
from django.utils import timezone
from twilio.rest import Client

from common.analytics import statsd
from common.enums import MessageDirectionType
from smsbot.models import SMSMessage


@shared_task
@statsd.timed("turnout.smsbot.tasks.send_welcome_sms")
def send_welcome_sms(number: str) -> None:
    from .models import Number

    n, _ = Number.objects.get_or_create(phone=number)

    # Note: If the user has opted-out (STOP), they won't receive this
    # message.  If they also sent UNSTOP or JOIN but not YES, they may
    # receive this message, but our record will still have an opt_out_time
    # since they didn't full opt back in.

    msg = (
        "Reply YES to join VoteAmerica and receive Election Alerts.\n"
        "Msg&Data rates may apply. 4 msgs/month.\n"
        "Reply HELP for help, STOP to cancel."
    )
    n.welcome_time = timezone.now()
    n.save()

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        to=number,
        messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
        body=msg,
    )
    SMSMessage.objects.create(
        phone=number, direction=MessageDirectionType.OUT, message=msg,
    )

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
        "Reminder: You are subscribed to VoteAmerica Election Alerts.\n"
        "Msg&Data rates may apply. 4 msgs/month.\n"
        "Reply HELP for help, STOP to cancel."
    )
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        to=number,
        messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
        body=msg,
    )
    SMSMessage.objects.create(
        phone=number, direction=MessageDirectionType.OUT, message=msg,
    )
