import datetime
import logging

from django.conf import settings
from django.core.cache import cache
from django.db.models import Max
from twilio.rest import Client

from common.rollouts import get_feature_int
from smsbot.models import Number

from .api_views import handle_incoming

logger = logging.getLogger("smsbot")


WATERMARK_CACHE_KEY = "smsbot_twilio_poll_last"


def get_watermark():
    last = cache.get(WATERMARK_CACHE_KEY, None)
    if last:
        return datetime.datetime.fromisoformat(last).replace(
            tzinfo=datetime.timezone.utc
        )

    last = Number.objects.aggregate(Max("opt_out_time")).get("opt_out_time__max")
    if last:
        # Add some slop here because the webhook timestamp is our
        # *local receive* time, not what twilio has recorded, so our
        # message timestamps (when delivered via webhook) are somewhat
        # inaccurate.  :(
        slop = get_feature_int("smsbot", "poll_slop_seconds") or 0
        return last - datetime.timedelta(seconds=slop)

    return datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
        seconds=get_feature_int("smsbot", "poll_max_seconds")
        or settings.SMS_OPTOUT_POLL_MAX_SECONDS
    )


def save_watermark(last):
    cache.set(WATERMARK_CACHE_KEY, last.isoformat())


def poll():
    since = get_watermark()
    start = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

    logger.debug(
        f"Checking incoming messages to {settings.SMS_OPTOUT_NUMBER} since {since}"
    )
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    messages = client.messages.list(
        to=settings.SMS_OPTOUT_NUMBER, date_sent_after=since,
    )
    messages.reverse()  # oldest to newest
    for msg in messages:
        n, reply = handle_incoming(msg.from_, msg.sid, msg.date_created, msg.body,)
        if reply:
            n.send_sms(reply)

    save_watermark(start)
