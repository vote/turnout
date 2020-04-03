from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import State, StateInformationFieldType
from .serializers import StateFieldSerializer, StateSerializer, FieldSerializer


class StateViewSet(ReadOnlyModelViewSet):
    model = State
    serializer_class = StateSerializer
    queryset = State.objects.all()

class StateFieldsViewSet(ReadOnlyModelViewSet):
    model = StateInformationFieldType
    
    queryset = StateInformationFieldType.objects.all()
    lookup_field = 'slug'

    def list(self, request):
        self.serializer_class = FieldSerializer
        return super().list(request)

    def retrieve(self, request, slug=None):
        self.serializer_class = StateFieldSerializer
        return super().retrieve(request, slug)