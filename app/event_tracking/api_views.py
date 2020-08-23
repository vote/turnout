from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from common import enums
from verifier.event_hooks import verifier_hooks

from .models import Event
from .serializers import EventSerializer


class TrackViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = Event
    serializer_class = EventSerializer
    queryset = Event.objects.all()

    def perform_create(self, serializer):
        obj = serializer.save()

        # Tool-specific hooks
        if self.request.GET.get("tool") == enums.ToolName.VERIFY.value:
            hook = verifier_hooks.get(obj.event_type)
            if hook:
                hook(
                    obj.action_id, obj.uuid,
                )
