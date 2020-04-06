import logging

from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common.enums import TurnoutRegistrationStatus
from election.models import State

from .models import Registration
from .serializers import RegistrationSerializer, StatusSerializer
from .tasks import process_registration_submission

logger = logging.getLogger("register")


class RegistrationViewSet(CreateModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = Registration
    serializer_class = RegistrationSerializer
    queryset = Registration.objects.filter(status=TurnoutRegistrationStatus.INCOMPLETE)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        return self.process_serializer(
            self.get_serializer(instance, data=request.data, partial=partial)
        )

    def create(self, request, *args, **kwargs):
        incomplete = request.GET.get("incomplete") == "true"
        return self.process_serializer(
            self.get_serializer(data=request.data, incomplete=incomplete)
        )

    def process_serializer(self, serializer):
        serializer.is_valid(raise_exception=True)
        if "state" in serializer.validated_data:
            serializer.validated_data["state"] = State.objects.get(
                code=serializer.validated_data["state"]
            )

        if "previous_state" in serializer.validated_data:
            serializer.validated_data["previous_state"] = State.objects.get(
                code=serializer.validated_data["previous_state"]
            )

        if "mailing_state" in serializer.validated_data:
            serializer.validated_data["mailing_state"] = State.objects.get(
                code=serializer.validated_data["mailing_state"]
            )

        if serializer.incomplete:
            serializer.validated_data["status"] = TurnoutRegistrationStatus.INCOMPLETE
        else:
            serializer.validated_data["status"] = TurnoutRegistrationStatus.PENDING

        # do not pass is_18_or_over or state_id_number to model, we are not storing it
        is_18_or_over = serializer.validated_data.pop("is_18_or_over", None)
        state_id_number = serializer.validated_data.pop("state_id_number", None)

        registration = serializer.save()

        response = {"uuid": registration.uuid}

        if not serializer.incomplete:
            process_registration_submission.delay(
                registration.uuid, state_id_number, is_18_or_over
            )

        return Response(response)


class StatusViewSet(UpdateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = Registration
    serializer_class = StatusSerializer
    queryset = Registration.objects.filter(status=TurnoutRegistrationStatus.INCOMPLETE)
