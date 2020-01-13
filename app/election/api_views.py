from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import State, StateInformationFieldType
from .serializers import StateSerializer, StateFieldSerializer


class StateViewSet(ReadOnlyModelViewSet):
    model = State
    serializer_class = StateSerializer
    queryset = State.objects.all()


class StateFieldsViewSet(ReadOnlyModelViewSet):
    model = StateInformationFieldType
    serializer_class = StateFieldSerializer
    queryset = StateInformationFieldType.objects.all()
