from rest_framework.viewsets import ReadOnlyModelViewSet

from cdn.views_mixin import CDNCachedView

from .models import State, StateInformationFieldType
from .serializers import FieldSerializer, StateFieldSerializer, StateSerializer


class StateViewSet(CDNCachedView, ReadOnlyModelViewSet):
    model = State
    serializer_class = StateSerializer
    queryset = State.states.all()


class StateFieldsViewSet(CDNCachedView, ReadOnlyModelViewSet):
    model = StateInformationFieldType

    queryset = StateInformationFieldType.objects.all()
    lookup_field = "slug"

    def list(self, request):
        self.serializer_class = FieldSerializer
        return super().list(request)

    def retrieve(self, request, slug=None):
        self.serializer_class = StateFieldSerializer
        return super().retrieve(request, slug)
