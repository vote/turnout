import datetime
import logging

from django.conf import settings
from django.core.cache import cache
from django.db.models import Max
from twilio.rest import Client

from smsbot.models import Number

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
        cmd = msg.body.strip().upper()
        if cmd in ["STOP"]:
            logger.info(f"Opt-out from {msg.from_} at {msg.date_created}")
            n, _ = Number.objects.get_or_create(phone=msg.from_)
            n.opt_out_time = msg.date_created
            n.opt_in_time = None
            n.save()
        if cmd in ["UNSTOP", "JOIN", "YES"]:
            logger.info(f"Opt-in from {msg.from_} at {msg.date_created}")
            n, _ = Number.objects.get_or_create(phone=msg.from_)
            n.opt_in_time = msg.date_created
            n.opt_out_time = None
            n.save()

    save_watermark(start)
