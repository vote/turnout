import logging
from typing import TYPE_CHECKING, Any, Dict

from rest_framework import serializers

from common import enums
from common.analytics import statsd

from .models import Client, SubscriberSlug

if TYPE_CHECKING:
    _Base = serializers.ModelSerializer
    from django.db.models import Model
else:
    _Base = object

logger = logging.getLogger("multi_tenant")


class SubscriberSerializerMixin(_Base):
    subscriber = serializers.PrimaryKeyRelatedField(read_only=True, required=False)
    _request_subscriber = None

    def create(self, validated_data: Dict[(str, Any)]) -> "Model":
        validated_data["subscriber"] = self.request_subscriber()
        return super().create(validated_data)

    def request_subscriber(self) -> Client:
        if self._request_subscriber:
            return self._request_subscriber

        request = self.context.get("request")
        if request and "subscriber" in request.GET:
            try:
                subscriber_slug = SubscriberSlug.objects.only("subscriber").get(
                    slug=request.GET["subscriber"],
                    subscriber__status=enums.SubscriberStatus.ACTIVE,
                )
                subscriber = subscriber_slug.subscriber
            except SubscriberSlug.DoesNotExist:
                logger.info(f'Invalid subscriber {request.GET["subscriber"]}')
                statsd.increment("turnout.multi_tenant.unknown_subscriber_request")
                subscriber = Client.objects.first()
        else:
            subscriber = Client.objects.first()

        self._request_subscriber = subscriber
        return subscriber
