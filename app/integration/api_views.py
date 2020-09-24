import logging

from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from common.analytics import statsd

from .tasks import process_lob_letter_status

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
    etype = request.data.get("event_type", {}).get("id")

    if not letter_id:
        logger.warning(f"Got lob webhook without object id: {request.data}")
        raise Http404

    process_lob_letter_status.delay(letter_id, etype)
    return HttpResponse()
