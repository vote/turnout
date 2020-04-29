from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import PartnerSlug


class PartnerSlugViewSet(GenericViewSet):
    permission_classes = [AllowAny]
    model = PartnerSlug
    queryset = PartnerSlug.objects.select_related("partner")
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        partner = instance.partner

        return Response(
            {
                "name": partner.name,
                "url": partner.url,
                "terms_of_service": partner.terms_of_service,
                "privacy_policy": partner.privacy_policy,
                "sms_enabled": partner.sms_enabled == True,
                "sms_checkbox_default": partner.sms_checkbox_default == True,
            }
        )
