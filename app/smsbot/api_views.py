import datetime
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from common.analytics import statsd
from common.enums import MessageDirectionType
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


@api_view(["POST"])
@permission_classes([AllowAny])
@validate_twilio_request
def twilio(request):
    number = request.data.get("From", None)
    body = request.data.get("Body", "")
    sid = request.data.get("MessageSid")
    if not number:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    n, created = Number.objects.get_or_create(phone=number)
    SMSMessage.objects.create(
        phone=n, direction=MessageDirectionType.IN, message=body, twilio_sid=sid,
    )

    cmd = body.lower().strip()
    if cmd in ["help"]:
        # Twilio advanced opt-in will always respond here.
        reply = None
    elif cmd in ["join"]:
        # Twilio advanced opt-in will respond here *if* they previously opted out.
        # We'll send an additional message either way.
        if n.opt_in_time:
            reply = (
                "You have already signed up for VoteAmerica Election Alerts. "
                "Reply HELP for help, STOP to cancel."
            )
        else:
            reply = (
                "Reply YES to join VoteAmerica and receive Election Alerts. "
                "Msg & Data rates may apply. 4 msgs/month. "
                "Reply HELP for help, STOP to cancel."
            )
    elif cmd in ["yes"]:
        if n.opt_in_time:
            reply = (
                "You have already signed up for VoteAmerica Election Alerts. "
                "Reply HELP for help, STOP to cancel."
            )
        else:
            reply = (
                "Thanks for joining VoteAmerica Election Alerts! "
                "Msg & Data rates may apply. 4 msgs/month. "
                "Reply HELP for help, STOP to cancel."
            )
            n.opt_in_time = timezone.now()
            n.opt_out_time = None
            n.save()
    elif cmd in ["stop"]:
        # Twilio advanced opt-in will always respond here.
        reply = None
        n.opt_out_time = timezone.now()
        n.opt_in_time = None
        n.save()
    else:
        if n.opt_in_time:
            reply = (
                "Hi, I am the VoteAmerica chat bot. Nice to hear from you again!\n"
                "HELP for help, STOP to cancel."
            )
        elif n.opt_out_time:
            # Twilio won't let them see this, but we can try anyway in case we are
            # out of sync with twilio's blacklist.
            reply = (
                "Hi, I am the VoteAmerica chat bot. "
                "You have previously opted-out of our Election Alerts list. "
                "Reply HELP for help, JOIN to join."
            )
        else:
            # We got a random message from an unknown number.
            reply = (
                "Hi, I am the VoteAmerica chat bot. "
                "Reply YES to join VoteAmerica and receive Election Alerts. "
                "Msg & Data rates may apply. 4 msgs/month. "
                "Reply HELP for help, STOP to cancel."
            )

    resp = MessagingResponse()
    if reply:
        reply_message = SMSMessage.objects.create(
            phone=n, direction=MessageDirectionType.OUT, message=reply,
        )
        resp.message(reply, action=reply_message.delivery_status_webhook())
    return HttpResponse(str(resp))


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
