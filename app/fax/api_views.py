import logging
from datetime import datetime
from typing import Optional

from django.core.files import File
from django.http import Http404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from smalluuid import SmallUUID
from typing_extensions import TypedDict

from common.analytics import statsd
from common.enums import FaxStatus
from turnout.celery_app import app

from .models import Fax
from .serializers import GatewayCallbackSerializer

logger = logging.getLogger("fax")

CallbackPayload = TypedDict(
    "CallbackPayload",
    {"fax_id": SmallUUID, "message": str, "timestamp": datetime, "status": FaxStatus},
)


def handle_fax_callback(data: CallbackPayload, fax: Fax):
    fax.status = data["status"]
    fax.status_message = data["message"]
    fax.status_timestamp = data["timestamp"]
    fax.save(update_fields=["status", "status_message", "status_timestamp"])

    if fax.status != FaxStatus.TEMPORARY_FAILURE:
        if fax.on_complete_task:
            app.send_task(
                fax.on_complete_task, args=[str(fax.status), fax.on_complete_task_arg]
            )


class GatewayCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(request.data)
        serializer = GatewayCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fax_id = serializer.validated_data["fax_id"]
        try:
            fax: Fax = Fax.objects.get(pk=fax_id)
        except Fax.DoesNotExist:
            statsd.increment("turnout.fax.callback.fax_does_not_exist")
            logger.warn(f"Got fax callback with nonexistant fax ID: {fax_id}")
            return Response({"error": "No such fax"}, status=status.HTTP_404_NOT_FOUND)

        token = request.GET.get("token")
        if not token:
            statsd.increment("turnout.fax.callback.no_token")
            logger.warn(f"Got fax callback with missing token for fax ID: {fax_id}")
            return Response(
                {"error": "Missing token"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not fax.validate_token(token):
            statsd.increment("turnout.fax.callback.wrong_token")
            logger.warn(f"Got fax callback with wrong token for fax ID: {fax_id}")
            return Response(
                {"error": "Token is incorrect"}, status=status.HTTP_403_FORBIDDEN
            )

        if fax.status_timestamp and (
            serializer.validated_data["timestamp"] < fax.status_timestamp
        ):
            statsd.increment("turnout.fax.callback.outdated_timestamp")
            logger.warn(
                f"Got fax callback with outdated timestamp {serializer.validated_data['timestamp']} for fax ID: {fax_id}"
            )
            return Response(
                {"warning": "Outdated timestamp; ignoring"}, status=status.HTTP_200_OK
            )

        handle_fax_callback(serializer.validated_data, fax)

        return Response({"ok": True}, status=status.HTTP_200_OK)
