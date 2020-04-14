import logging
from typing import TYPE_CHECKING, Any, Dict

from rest_framework import serializers

from common.analytics import statsd

from .models import Client, PartnerSlug

if TYPE_CHECKING:
    _Base = serializers.ModelSerializer
    from django.db.models import Model
else:
    _Base = object

logger = logging.getLogger("multi_tenant")


class PartnerSerializerMixin(_Base):
    partner = serializers.PrimaryKeyRelatedField(read_only=True, required=False)

    def create(self, validated_data: Dict[(str, Any)]) -> "Model":
        request = self.context.get("request")
        if request and "partner" in request.GET:
            try:
                partner_slug = PartnerSlug.objects.only("partner").get(
                    slug=request.GET["partner"]
                )
                partner = partner_slug.partner
            except PartnerSlug.DoesNotExist:
                logger.info(f'Invalid partner {request.GET["partner"]}')
                statsd.increment("turnout.multi_tenant.unknown_partner_request")
                partner = Client.objects.first()
        else:
            partner = Client.objects.first()

        validated_data["partner"] = partner
        return super().create(validated_data)
