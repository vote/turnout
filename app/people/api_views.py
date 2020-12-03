from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from integration.tasks import (
    unsubscribe_email_from_actionnetwork,
    unsubscribe_phone_from_actionnetwork,
)

from .serializers import OptInOutSerializer


class OptOutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = OptInOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data.get("phone")
        email = serializer.validated_data.get("email")

        if email:
            unsubscribe_email_from_actionnetwork.delay(email)
            if phone:
                unsubscribe_phone_from_actionnetwork.delay(str(phone), email)
        elif phone:
            unsubscribe_phone_from_actionnetwork.delay(str(phone))

        return Response()
