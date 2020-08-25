import json
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from action.models import Action
from common.analytics import statsd
from common.enums import EventType

logger = logging.getLogger("integration")


# see https://www.lob.com/guides#webhooks_block
def validate_lob_request(func):
    def wrapper(request, *args, **kwargs):
        import hashlib
        import hmac
        import base64

        timestamp = request.headers.get("Lob-Signature-Timestamp", "")
        message = timestamp + "." + request.body.decode("utf-8")
        secret = settings.LOB_LETTER_WEBHOOK_SECRET
        signature = base64.b64encode(
            hmac.new(
                secret.encode("utf-8"),
                message.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
        )

        if signature != request.headers.get("Lob-Signature"):
            statsd.increment("turnout.integration.bad_lob_signature")
            logger.warning(
                f"Bad lob signature, headers {request.headers}, data {request.data}"
            )
            return HttpResponse("Bad lob signature", status=status.HTTP_403_FORBIDDEN)
        return func(request, *args, **kwargs)

    return wrapper


@api_view(["POST"])
@permission_classes([AllowAny])
@validate_lob_request
def lob_letter_status(request, pk):

    event_mapping = {
        "letter.mailed": EventType.LOB_MAILED,
        "letter.processed_for_delivery": EventType.LOB_PROCESSED_FOR_DELIVERY,
        "letter.re-routed": EventType.LOB_REROUTED,
        "letter.returned_to_sender": EventType.LOB_RETURNED,
    }
    event_sms = {
        #        "letter.mailed": "Your absentee ballot application has been mailed. Expect delivery in 2-4 days.",
        #        "letter.processed_for_delivery": "Your absentee ballot application should be delivered in the next 24 hours",
        #        "letter.returned_to_sender": "Unfortunately, your absentee ballot application has been returned to sender.",
    }

    try:
        action = Action.objects.get(pk=pk)
        info = json.loads(request.body)
        etype = info.get("event_type", {}).get("id")
        if etype in event_mapping:
            action.track_event(event_mapping[etype])
        if etype in event_sms:
            number = event.get_sms_number()
            if number:
                number.send_sms(event_sms[etype])
    except ObjectDoesNotExist:
        return HttpResponse("Event id not found", status=status.HTTP_404_NOT_FOUND)
    return HttpResponse()
