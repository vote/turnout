import logging

from enumfields.drf.fields import EnumField
from enumfields.drf.serializers import EnumSupportSerializerMixin
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from action.serializers import ActionSerializer
from common import enums
from common.utils.fields import RequiredBooleanField
from common.utils.serializers import TrackingSerializer
from common.validators import (
    must_be_true_validator,
    state_code_validator,
    zip_validator,
)
from election.choices import STATES

from .models import Registration

logger = logging.getLogger("register")


class RegistrationSerializer(TrackingSerializer, ActionSerializer):
    phone = PhoneNumberField(required=False)
    zipcode = serializers.CharField(validators=[zip_validator], required=True)
    previous_zipcode = serializers.CharField(validators=[zip_validator], required=False)
    mailing_zipcode = serializers.CharField(validators=[zip_validator], required=False)
    state = serializers.ChoiceField(
        choices=STATES, validators=[state_code_validator], required=True
    )
    previous_state = serializers.ChoiceField(
        choices=STATES, validators=[state_code_validator], required=False
    )
    mailing_state = serializers.ChoiceField(
        choices=STATES, validators=[state_code_validator], required=False
    )
    title = serializers.CharField(required=True)
    previous_title = serializers.CharField(required=True)
    state_id_number = serializers.CharField(required=False)
    is_18_or_over = RequiredBooleanField(
        required=False, validators=[must_be_true_validator]
    )
    us_citizen = RequiredBooleanField(
        required=False, validators=[must_be_true_validator]
    )

    class Meta:
        model = Registration
        minimum_necessary_fields = [
            "title",
            "first_name",
            "last_name",
            "address1",
            "city",
            "state",
            "zipcode",
            "date_of_birth",
            "email",
        ]
        nationally_required_fields = ["state_id_number", "us_citizen", "is_18_or_over"]
        optional_fields = [
            "subscriber",
            "suffix",
            "phone",
            "sms_opt_in",
            "sms_opt_in_subscriber",
            "address2",
            "previous_title",
            "previous_first_name",
            "previous_middle_name",
            "previous_last_name",
            "previous_suffix",
            "previous_address1",
            "previous_address2",
            "previous_city",
            "previous_state",
            "previous_zipcode",
            "mailing_address1",
            "mailing_address2",
            "mailing_city",
            "mailing_state",
            "mailing_zipcode",
            "gender",
            "race_ethnicity",
            "party",
            "source",
            "utm_campaign",
            "utm_source",
            "utm_medium",
            "utm_term",
            "utm_content",
            "embed_url",
            "session_id",
            "referring_tool",
        ]


class StatusSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    status = EnumField(enum=enums.TurnoutActionStatus, required=True)

    class Meta:
        model = Registration
        fields = ("status",)

    def validate_status(self, value):
        if not value == enums.TurnoutActionStatus.OVR_REFERRED:
            raise serializers.ValidationError(
                f"Registration status can only be {enums.TurnoutActionStatus.OVR_REFERRED.value}"
            )
        return value
