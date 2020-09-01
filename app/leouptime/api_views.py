from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination

from .models import Site, SiteCheck, SiteDowntime
from .serializers import SiteCheckSerializer, SiteDowntimeSerializer, SiteSerializer


class PaginationStyle(LimitOffsetPagination):
    default_limit = 100


class SiteList(generics.ListAPIView):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    pagination_class = PaginationStyle


class SiteDownList(generics.ListAPIView):
    queryset = Site.objects.filter(state_up=False)
    serializer_class = SiteSerializer
    pagination_class = PaginationStyle


class SiteDetail(generics.RetrieveAPIView):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer


class SiteChecksList(generics.ListAPIView):
    serializer_class = SiteCheckSerializer
    pagination_class = PaginationStyle

    def get_queryset(self):
        return SiteCheck.objects.filter(site_id=self.kwargs["pk"])

class SiteDowntimeList(generics.ListAPIView):
    serializer_class = SiteDowntimeSerializer
    pagination_class = PaginationStyle

    def get_queryset(self):
        return SiteDowntime.objects.filter(site_id=self.kwargs["pk"])


class SiteCheckDetail(generics.RetrieveAPIView):
    queryset = SiteCheck.objects.all()
    serializer_class = SiteCheckSerializer


class DowntimeList(generics.ListAPIView):
    queryset = SiteDowntime.objects.all()
    serializer_class = SiteDowntimeSerializer
    pagination_class = PaginationStyle
