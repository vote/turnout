from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import ApiKeyAuthentication, ApiKeyRequired


class CheckView(APIView):
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [ApiKeyRequired]

    def get(self, request):
        return Response(
            {"ok": True, "subscriber": request.auth.subscriber.slug},
            status=status.HTTP_200_OK,
        )
