from django.core.files import File
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from smalluuid import SmallUUID

from common import enums
from common.analytics import statsd
from common.utils.serializers import SmallUUIDKeySerializer

from .models import SecureUploadItem, StorageItem
from .parsers import UnnamedFileUploadParser


class ResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SmallUUIDKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            item = StorageItem.objects.get(pk=serializer.validated_data["id"],)
        except StorageItem.DoesNotExist:
            statsd.increment("turnout.storage.reset_failure_missing")
            raise Http404

        item.refresh_token()
        # TODO: Trigger email to user with new token

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
