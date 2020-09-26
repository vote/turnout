from rest_framework.viewsets import ReadOnlyModelViewSet

from cdn.views_mixin import CDNCachedView

from .models import State, StateInformationFieldType
from .serializers import FieldSerializer, StateFieldSerializer, StateSerializer


class StateViewSet(CDNCachedView, ReadOnlyModelViewSet):
    model = State
    serializer_class = StateSerializer
    queryset = State.states.all()

    def list(self, request):
        response = super().list(request)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    def retrieve(self, request, pk=None):
        response = super().retrieve(request, pk=pk)
        response["Access-Control-Allow-Origin"] = "*"
        return response


class StateFieldsViewSet(CDNCachedView, ReadOnlyModelViewSet):
    model = StateInformationFieldType

    queryset = StateInformationFieldType.objects.all()
    lookup_field = "slug"

    def list(self, request):
        self.serializer_class = FieldSerializer
        response = super().list(request)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    def retrieve(self, request, slug=None):
        self.serializer_class = StateFieldSerializer
        response = super().retrieve(request, slug)
        response["Access-Control-Allow-Origin"] = "*"
        return response
