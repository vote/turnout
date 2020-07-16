from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from action.serializers import ActionSerializer
from common.utils.serializers import TrackingSerializer
from common.validators import state_code_validator
from election.choices import STATES

from .models import Lookup, zip_validator


class LookupSerializer(TrackingSerializer, ActionSerializer):
    phone = PhoneNumberField(required=False)
    zipcode = serializers.CharField(validators=[zip_validator])
    state = serializers.ChoiceField(
        choices=STATES, required=True, validators=[state_code_validator]
    )

    class Meta:
        model = Lookup
        minimum_necessary_fields = [
            "first_name",
            "last_name",
            "address1",
            "city",
            "state",
            "zipcode",
            "date_of_birth",
            "email",
        ]
        optional_fields = [
            "address2",
            "age",
            "phone",
            "sms_opt_in",
            "sms_opt_in_subscriber",
            "last_updated",
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
