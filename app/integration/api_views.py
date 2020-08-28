import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from common.analytics import statsd
from common.enums import EventType, ExternalToolType
from smsbot.models import Number

from .models import Link

logger = logging.getLogger("integration")


# see https://www.lob.com/guides#webhooks_block
def validate_lob_request(func):
    def wrapper(request, *args, **kwargs):
        import hashlib
        import hmac

        timestamp = request.headers.get("Lob-Signature-Timestamp", "")
        message = timestamp + "." + request.body.decode("utf-8")
        secret = settings.LOB_LETTER_WEBHOOK_SECRET
        signature = hmac.new(
            secret.encode("utf-8"), message.encode("utf-8"), digestmod=hashlib.sha256,
        ).hexdigest()
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
def lob_letter_status(request):
    letter_id = request.data.get("body", {}).get("id")
    if not letter_id:
        logger.warning(f"Got lob webhook without object id: {request.data}")
        raise Http404

    link = None
    for link in Link.objects.filter(
        external_tool=ExternalToolType.LOB, external_id=letter_id
    ):
        break
    if not link:
        logger.warning(f"Got lob webhook on unknown letter id {letter_id}")
        raise Http404
    action = link.action

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

    etype = request.data.get("event_type", {}).get("id")

    item = action.get_source_item()
    logger.info(f"Received lob status update on {item} of {etype}")

    if etype in event_mapping:
        action.track_event(event_mapping[etype])

    if etype in event_sms:
        if item.phone:
            try:
                number = Number.objects.get(phone=item.phone)
                number.send_sms(event_sms[etype])
            except ObjectDoesNotExist:
                pass

    return HttpResponse()
