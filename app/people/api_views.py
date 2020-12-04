from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from integration.tasks import (
    change_actionnetwork_name,
    unsubscribe_email_from_actionnetwork,
    unsubscribe_phone_from_actionnetwork,
)

from .models import NameOverride
from .serializers import NameOverrideSerializer, OptInOutSerializer


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


class NameOverrideViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = NameOverride
    serializer_class = NameOverrideSerializer
    queryset = NameOverride.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        change_actionnetwork_name.delay(
            email=serializer.validated_data.get("email"),
            first_name=serializer.validated_data.get("first_name"),
            last_name=serializer.validated_data.get("last_name"),
        )

        return Response()
