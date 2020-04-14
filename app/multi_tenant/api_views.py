from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from .models import PartnerSlug
from .serializers import PartnerSlugSerializer


class PartnerSlugViewSet(RetrieveModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = PartnerSlug
    serializer_class = PartnerSlugSerializer
    queryset = PartnerSlug.objects.select_related("partner")
    lookup_field = "slug"
