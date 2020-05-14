from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common import enums
from common.enums import TurnoutActionStatus
from election.models import State


class IncompleteActionViewSet(CreateModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        action_object = self.process_serializer(
            self.get_serializer(instance, data=request.data, partial=partial)
        )
        response = {"uuid": action_object.uuid, "action_id": action_object.action.pk}
        return Response(response)

    def create(self, request, *args, **kwargs):
        incomplete = request.GET.get("incomplete") == "true"
        action_object = self.process_serializer(
            self.get_serializer(data=request.data, incomplete=incomplete)
        )
        response = {"uuid": action_object.uuid, "action_id": action_object.action.pk}
        return Response(response)

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
            serializer.validated_data["status"] = TurnoutActionStatus.INCOMPLETE
        else:
            serializer.validated_data["status"] = TurnoutActionStatus.PENDING

        # do not pass is_18_or_over or state_id_number to model, we are not storing it
        is_18_or_over = serializer.validated_data.pop("is_18_or_over", None)
        state_id_number = serializer.validated_data.pop("state_id_number", None)

        action_object = serializer.save()

        if serializer.incomplete:
            action_object.action.track_event(enums.EventType.START)

        if not serializer.incomplete:
            self.task.delay(action_object.uuid, state_id_number, is_18_or_over)

        return action_object
