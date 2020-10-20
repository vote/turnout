import logging

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Region
from .serializers import RegionDetailSerializer, RegionNameSerializer

logger = logging.getLogger("official")


class StateRegionsViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    model = Region
    serializer_class = RegionNameSerializer

    def get_queryset(self):
        state_code = self.kwargs["state"]
        queryset = Region.visible.filter(state__code=state_code).order_by("name")

        county = self.request.query_params.get("county", None)
        if county:
            queryset = queryset.filter(county=county)

        municipality = self.request.query_params.get("municipality", None)
        if municipality:
            queryset = queryset.filter(municipality=municipality)

        return queryset


class RegionDetailViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    model = Region
    serializer_class = RegionDetailSerializer
    queryset = Region.objects.all()
    lookup_field = "external_id"


@api_view(["GET"])
def address_regions(request):
    return Response(
        {"alert": "This resource has been disabled."}, status=status.HTTP_404_NOT_FOUND
    )
