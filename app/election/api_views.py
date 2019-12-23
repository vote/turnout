from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import State
from .serializers import StateSerializer


class StateViewSet(ReadOnlyModelViewSet):
    model = State
    serializer_class = StateSerializer
    queryset = State.objects.all()
