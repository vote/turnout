from django.http import Http404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.analytics import statsd
from common.utils.serializers import SmallUUIDKeySerializer

from .models import StorageItem


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
