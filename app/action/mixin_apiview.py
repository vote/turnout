from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common import enums
from common.apm import tracer
from common.enums import TurnoutActionStatus
from election.models import State


class IncompleteActionViewSet(CreateModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        incomplete = request.GET.get("incomplete") == "true"
        instance = self.get_object()
        action_object = self.process_serializer(
            self.get_serializer(
                instance, data=request.data, partial=partial, incomplete=incomplete
            ),
            is_create=False,
        )

        return self.create_or_update_response(action_object)

    def create(self, request, *args, **kwargs):
        incomplete = request.GET.get("incomplete") == "true"
        action_object = self.process_serializer(
            self.get_serializer(data=request.data, incomplete=incomplete),
            is_create=True,
        )

        return self.create_or_update_response(action_object)

    def after_create(self, action_object):
        pass

    def after_update(self, action_object):
        pass

    def after_create_or_update(self, action_object):
        pass

    def after_validate(self, serializer):
        pass

    def create_or_update_response(self, action_object):
        response = {"uuid": action_object.uuid, "action_id": action_object.action.pk}
        return Response(response)

    def complete(
        self,
        serializer,
        action_object,
        state_id_number,
        state_id_number_2,
        is_18_or_over,
    ):
        # NOTE: we drop state_id_number_2 on the floor here since only register needs it, and it overrides
        # this method.
        serializer.validated_data["status"] = TurnoutActionStatus.PENDING
        action_object.save()

        self.after_complete(action_object, state_id_number, is_18_or_over)

    def after_complete(self, action_object, state_id_number, is_18_or_over):
        pass

    @tracer.wrap()
    def process_serializer(self, serializer, is_create):
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

        if not is_create:
            # Forbid changing email or phone (but don't error, for backwards
            # compatiblity)
            serializer.validated_data.pop("email", None)
            serializer.validated_data.pop("phone", None)

        # do not pass is_18_or_over or state_id_number to model, we are not storing it
        is_18_or_over = serializer.validated_data.pop("is_18_or_over", None)
        state_id_number = serializer.validated_data.pop("state_id_number", None)
        state_id_number_2 = serializer.validated_data.pop("state_id_number_2", None)

        serializer.validated_data["status"] = TurnoutActionStatus.INCOMPLETE

        initial_events = serializer.validated_data.pop("initial_events", [])

        self.after_validate(serializer)

        action_object = serializer.save()

        if is_create:
            self.after_create(action_object)
        else:
            self.after_update(action_object)

        self.after_create_or_update(action_object)

        if serializer.incomplete:
            action_object.action.track_event(enums.EventType.START)
        else:
            self.complete(
                serializer,
                action_object,
                state_id_number,
                state_id_number_2,
                is_18_or_over,
            )

        for event_type in initial_events:
            action_object.action.track_event(event_type)

        return action_object
