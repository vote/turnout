import logging

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from action.serializers import ActionSerializer
from common.utils.fields import RequiredBooleanField
from common.utils.serializers import TrackingSerializer
from common.validators import (
    must_be_true_validator,
    state_code_validator,
    zip_validator,
)
from election.choices import STATES

from .models import BallotRequest

logger = logging.getLogger("absentee")


class BallotRequestSerializer(TrackingSerializer, ActionSerializer):
    phone = PhoneNumberField(required=False)
    zipcode = serializers.CharField(validators=[zip_validator], required=True)
    mailing_zipcode = serializers.CharField(validators=[zip_validator], required=False)
    state = serializers.ChoiceField(
        choices=STATES, validators=[state_code_validator], required=True
    )
    mailing_state = serializers.ChoiceField(
        choices=STATES, validators=[state_code_validator], required=False
    )
    state_id_number = serializers.CharField(required=False)
    is_18_or_over = RequiredBooleanField(
        required=False, validators=[must_be_true_validator]
    )
    us_citizen = RequiredBooleanField(
        required=False, validators=[must_be_true_validator]
    )

    class Meta:
        model = BallotRequest
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
        nationally_required_fields = ["us_citizen", "is_18_or_over", "region"]
        optional_fields = [
            "state_id_number",
            "subscriber",
            "suffix",
            "middle_name",
            "phone",
            "sms_opt_in",
            "sms_opt_in_subscriber",
            "address2",
            "mailing_address1",
            "mailing_address2",
            "mailing_city",
            "mailing_state",
            "mailing_zipcode",
            "state_fields",
            "source",
            "utm_campaign",
            "utm_source",
            "utm_medium",
            "utm_term",
            "utm_content",
            "embed_url",
            "session_id",
            "email_referrer",
            "mobile_referrer",
            "signature",
            "submit_date",
        ]
