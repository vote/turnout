from rest_framework import serializers

from action.serializers import ActionSerializer
from common.utils.serializers import TrackingSerializer
from common.validators import zip_validator

from .models import PollingPlaceLookup


class PollingPlaceLookupReportSerializer(TrackingSerializer, ActionSerializer):
    zipcode = serializers.CharField(validators=[zip_validator])
    source_result = serializers.JSONField(write_only=True, allow_null=True)
    source_status = serializers.CharField(write_only=True, allow_null=True)

    def create(self, validated_data):
        validated_data["dnc_result"] = validated_data.pop("source_result", None)
        validated_data["dnc_status"] = validated_data.pop("source_status", None)
        return super().create(validated_data)

    class Meta:
        model = PollingPlaceLookup
        minimum_necessary_fields = [
            "unstructured_address",
        ]
        optional_fields = [
            "source_result",
            "source_status",
            "civic_status",
            "civic_result",
            "utm_campaign",
            "utm_source",
            "utm_medium",
            "utm_term",
            "utm_content",
            "source",
            "embed_url",
            "session_id",
            "email_referrer",
            "mobile_referrer",
        ]
