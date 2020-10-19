from rest_framework import serializers

from action.serializers import ActionSerializer
from common.utils.serializers import TrackingSerializer
from common.validators import zip_validator

from .models import PollingPlaceLookup


class PollingPlaceLookupReportSerializer(TrackingSerializer, ActionSerializer):
    zipcode = serializers.CharField(validators=[zip_validator])

    class Meta:
        model = PollingPlaceLookup
        minimum_necessary_fields = [
            "unstructured_address",
        ]
        optional_fields = [
            "dnc_status",
            "dnc_result",
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
