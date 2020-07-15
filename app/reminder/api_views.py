from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from election.models import State

from .models import ReminderRequest
from .serializers import ReminderRequestSerializer


class ReminderRequestViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = ReminderRequest
    serializer_class = ReminderRequestSerializer
    queryset = ReminderRequest.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.validated_data["state"] = State.objects.get(
            code=serializer.validated_data["state"]
        )

        instance = serializer.save()

        response = {"action_id": instance.action.pk}

        return Response(response)
