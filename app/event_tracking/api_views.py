from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from .models import Event
from .serializers import EventSerializer


class TrackViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = Event
    serializer_class = EventSerializer
    queryset = Event.objects.all()
