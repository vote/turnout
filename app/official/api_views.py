from rest_framework import mixins, viewsets

from .models import Address, Office, Region
from .serializers import RegionDetailSerializer, RegionNameSerializer


class StateRegionsViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    model = Region
    serializer_class = RegionNameSerializer

    def get_queryset(self):
        state_code = self.kwargs["state"]
        queryset = Region.objects.filter(state__code=state_code)

        county = self.request.query_params.get("county", None)
        if county:
            queryset = queryset.filter(county=county)

        municipality = self.request.query_params.get("municipality", None)
        if municipality:
            queryset = queryset.filter(municipality=municipality)

        absentee = self.request.query_params.get("absentee", False)
        if absentee:
            # return only regions with office addresses which process absentee ballots
            absentee_addresses = Address.objects.filter(process_absentee_requests=True)
            absentee_office_ids = absentee_addresses.values_list("office")
            absentee_offices = Office.objects.filter(
                external_id__in=absentee_office_ids
            )
            absentee_region_ids = absentee_offices.values_list("region")
            queryset = queryset.filter(external_id__in=absentee_region_ids)

            # this should work, but does not for MI/WI because of data quality issues
            # in those cases, keep only city/municipal offices, but limit out countywide
            if state_code in ["MI", "WI"]:
                queryset = queryset.exclude(municipality__isnull=True)

        return queryset


class RegionDetailViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    model = Region
    serializer_class = RegionDetailSerializer
    queryset = Region.objects.all()
    lookup_field = "external_id"
