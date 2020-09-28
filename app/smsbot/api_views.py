import datetime
import logging
from typing import Tuple

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from common.analytics import statsd
from common.enums import MessageDirectionType
from common.rollouts import get_feature_int, get_feature_str
from integration.actionnetwork import resubscribe_phone
from smsbot.models import Number, SMSMessage

"""
Twilio's advanced opt-in should be configured with these messages:

-- Opt-out --
Default keywords: stop
Extra keywords:

  You will no longer receive messages from VoteAmerica. Goodbye! Reply HELP for help, JOIN to join.

-- Opt-in --
Default keywords: start, unstop
Extra keywords: join, yes

  Welcome back!

(Twilio will send this *only* if they previously opted-out.)
(The bot will send more instructions below)

-- Help --
Default keywords: help

  Reply YES to receive VoteAmerica Election Alerts.
  Msg & Data Rates May Apply. 4 msgs/month.
  Reply HELP for help, STOP to cancel.

"""


logger = logging.getLogger("smsbot")


def validate_twilio_request(func):
    def wrapper(request, *args, **kwargs):
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        url = settings.PRIMARY_ORIGIN + request.get_full_path()
        if not validator.validate(
            url, request.data, request.headers.get("X-Twilio-Signature", ""),
        ):
            statsd.increment("turnout.smsbot.bad_twilio_signature")
            logger.warning(
                f"Bad twilio callback signature, url {url}, headers {request.headers}, request {request.data}"
            )
            return HttpResponse(
                "Bad twilio signature", status=status.HTTP_403_FORBIDDEN
            )
        return func(request, *args, **kwargs)

    return wrapper


def handle_incoming(
    from_number: str, sid: str, date_created: datetime.datetime, body: str,
) -> Tuple[Number, str]:
    n, created = Number.objects.get_or_create(phone=from_number)
    if created:
        logger.info(f"New {n}")

    if SMSMessage.objects.filter(phone=n, twilio_sid=sid).exists():
        logger.debug(f"Ignoring duplicate {n} at {date_created} {sid}: {body}")
        return n, None

    logger.debug(f"Handling {n} at {date_created} {sid}: {body}")
    SMSMessage.objects.create(
        phone=n, direction=MessageDirectionType.IN, message=body, twilio_sid=sid,
    )

    cmd = body.strip().upper()
    reply = None
    if cmd in ["STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"]:
        logger.info(f"Opt-out from {n} at {date_created}")
        n.opt_out_time = date_created
        n.opt_in_time = None
        n.save()
    elif cmd in ["JOIN"]:
        logger.info(f"Opt-in from {n} at {date_created}")
        n.opt_in_time = date_created
        n.opt_out_time = None
        n.save()

        reply = (
            get_feature_str("smsbot", "autoreply_joined")
            or "Thank you for subscribing to VoteAmerica election alerts. Reply STOP to cancel."
        )

        # Try to match this to an ActionNetwork subscriber.  Note that this will may fail if the number
        # has been used more than once.
        resubscribe_phone(n.phone)
    elif cmd in ["HELP", "INFO"]:
        # ActionNetwork handles this
        pass
    else:
        # check last
        try:
            last = (
                SMSMessage.objects.filter(phone=n, direction=MessageDirectionType.OUT)
                .exclude(twilio_sid=sid)
                .latest("created_at")
            )
        except SMSMessage.DoesNotExist:
            last = None

        throttle = (
            get_feature_int("smsbot", "autoreply_throttle_minutes")
            or settings.SMS_AUTOREPLY_THROTTLE_MINUTES
        )

        if n.opt_out_time:
            reply = get_feature_str("smsbot", "autoreply_opted_out") or (
                "You have previously opted-out of VoteAmerica election alerts. "
                "Reply HELP for help, JOIN to re-join."
            )
        else:
            reply = get_feature_str("smsbot", "autoreply") or (
                "Thanks for contacting VoteAmerica. "
                "For more information or assistance visit https://voteamerica.com/faq/ "
                "or text STOP to opt-out."
            )

        if (
            last
            and last.created_at
            >= datetime.datetime.now(tz=datetime.timezone.utc)
            - datetime.timedelta(minutes=throttle)
            and last.message == reply
        ):
            logger.info(
                f"Ignoring {n} at {date_created} (last autoreply at {last.created_at}): {body}"
            )
            reply = None
        else:
            logger.info(f"Auto-reply to {n} at {date_created}: {body}")

    return n, reply


@api_view(["POST"])
@permission_classes([AllowAny])
@validate_twilio_request
def twilio(request):
    number = request.data.get("From", None)
    body = request.data.get("Body", "")
    sid = request.data.get("MessageSid")

    if not number:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    date_created = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    n, reply = handle_incoming(number, sid, date_created, body)

    resp = MessagingResponse()
    if reply:
        reply_message = SMSMessage.objects.create(
            phone=n, direction=MessageDirectionType.OUT, message=reply,
        )
        resp.message(reply, action=reply_message.delivery_status_webhook())
    return HttpResponse(str(resp), content_type="application/xml")


@api_view(["POST"])
@permission_classes([AllowAny])
@validate_twilio_request
def twilio_message_status(request, pk):
    try:
        message = SMSMessage.objects.get(pk=pk)
        message.status = request.data.get("MessageStatus")
        message.status_time = datetime.datetime.now(tz=datetime.timezone.utc)
        message.save()
    except ObjectDoesNotExist:
        return HttpResponse("Message id not found", status=status.HTTP_404_NOT_FOUND)
    return HttpResponse()
