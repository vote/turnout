from datetime import datetime, timezone

from enumfields.drf.fields import EnumField
from rest_framework import serializers

from common import enums


class TimestampField(serializers.Field):
    def to_representation(self, value):
        return int(value.timestamp())

    def to_internal_value(self, value):
        return datetime.fromtimestamp(value, tz=timezone.utc)


class GatewayCallbackSerializer(serializers.Serializer):
    fax_id = serializers.UUIDField(required=True)
    status = EnumField(enum=enums.FaxStatus, required=True)
    message = serializers.CharField(required=True)
    timestamp = TimestampField(required=True)
