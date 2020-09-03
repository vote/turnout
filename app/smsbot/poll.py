import datetime
import logging

from django.conf import settings
from django.core.cache import cache
from django.db.models import Max
from twilio.rest import Client

from common.enums import MessageDirectionType
from integration.actionnetwork import resubscribe_phone
from smsbot.models import Number, SMSMessage

logger = logging.getLogger("smsbot")


WATERMARK_CACHE_KEY = "smsbot_twilio_poll_last"


def get_watermark():
    last = cache.get(WATERMARK_CACHE_KEY, None)
    if last:
        return datetime.datetime.fromisoformat(last)

    last = Number.objects.aggregate(Max("opt_out_time")).get("opt_out_time__max")
    if last:
        return last

    return datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
        seconds=settings.SMS_OPTOUT_POLL_MAX_SECONDS
    )


def save_watermark(last):
    cache.set(WATERMARK_CACHE_KEY, last.isoformat())


def poll():
    since = get_watermark()
    start = datetime.datetime.now()

    logger.info(
        f"Checking incoming messages to {settings.SMS_OPTOUT_NUMBER} since {since}"
    )
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    messages = client.messages.list(
        to=settings.SMS_OPTOUT_NUMBER, date_sent_after=since,
    )
    messages.reverse()  # oldest to newest
    for msg in messages:
        logger.debug(f"msg {msg.from_} {msg.date_created} {msg.body}")
        n, _ = Number.objects.get_or_create(phone=msg.from_)
        if SMSMessage.objects.filter(phone=n, twilio_sid=msg.sid).exists():
            continue
        SMSMessage.objects.create(
            phone=n,
            direction=MessageDirectionType.IN,
            message=msg.body,
            twilio_sid=msg.sid,
        )
        cmd = msg.body.strip().upper()
        if cmd in ["STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"]:
            logger.info(f"Opt-out from {msg.from_} at {msg.date_created}")
            n.opt_out_time = msg.date_created
            n.opt_in_time = None
            n.save()
        elif cmd in ["JOIN"]:
            logger.info(f"Opt-in from {msg.from_} at {msg.date_created}")
            n.opt_in_time = msg.date_created
            n.opt_out_time = None
            n.save()

            n.send_sms(
                "Thank you for subscribing to VoteAmerica election alerts. Reply STOP to cancel."
            )

            # Try to match this to an ActionNetwork subscriber.  Note that this will may fail if the number
            # has been used more than once.
            resubscribe_phone(n.phone)
        elif cmd in ["HELP", "INFO"]:
            # ActionNetwork handles this
            pass
        else:
            logger.info(f"Auto-reply to {msg.from_} at {msg.date_created}: {msg.body}")
            if n.opt_out_time:
                n.send_sms(
                    "You have previously opted-out of VoteAmerica election alerts. "
                    "Reply HELP for help, JOIN to re-join."
                )
            else:
                n.send_sms(
                    "Thanks for contacting VoteAmerica. "
                    "For more information or assistance visit https://voteamerica.com/faq/ "
                    "or text STOP to opt-out."
                )

    save_watermark(start)
