import logging
from uuid import UUID

from django.core.files import File
from django.http import Http404, HttpResponseRedirect
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from smalluuid import SmallUUID

from common import enums
from common.analytics import statsd

from .models import SecureUploadItem, StorageItem
from .notification import trigger_notification
from .parsers import UnnamedFileUploadParser

logger = logging.getLogger("storage")


class ResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uuid_or_smalluuid = request.data.get("id")
        if not uuid_or_smalluuid:
            raise serializers.ValidationError({"id": "Required"})

        try:
            uuid = UUID(uuid_or_smalluuid)
        except (TypeError, ValueError):
            try:
                uuid = UUID(SmallUUID(uuid_or_smalluuid).hex_grouped)
            except (TypeError, ValueError):
                raise serializers.ValidationError({"id": "Must be a uuid or smalluuid"})

        try:
            item = StorageItem.objects.get(pk=uuid)
        except StorageItem.DoesNotExist:
            statsd.increment("turnout.storage.reset_failure_missing")
            raise Http404

        if item.purged:
            logger.info(f"Purged file at {item.purged}. Redirecting.")
            return HttpResponseRedirect(item.purged_url)

        if not item.validate_token(str(item.token)):
            # Only refresh the token if it's expired
            item.refresh_token()

        trigger_notification(item)

        return Response(status=status.HTTP_201_CREATED)


class SecureUploadView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [UnnamedFileUploadParser]

    def post(self, request):
        upload_type = request.GET.get("upload_type")
        if not upload_type or (
            upload_type not in [label for _, label in enums.SecureUploadType.choices()]
        ):
            return Response(
                {
                    "upload_type": [
                        "Must provide a valid upload_type as a URL parameter"
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.content_type:
            return Response(
                {"Content-Type": ["Must provide a valid Content-Type header"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = SecureUploadItem(
            upload_type=upload_type, content_type=request.content_type
        )
        item.file.save(
            str(SmallUUID()), File(request.data["file"]), True,
        )

        return Response({"uuid": item.uuid})
