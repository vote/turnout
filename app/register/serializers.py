import logging

from enumfields.drf.fields import EnumField
from enumfields.drf.serializers import EnumSupportSerializerMixin
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from action.models import Action
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
    declaration = RequiredBooleanField(
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
        nationally_required_fields = [
            "state_id_number",
            "us_citizen",
            "is_18_or_over",
        ]
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
            "email_referrer",
            "mobile_referrer",
            "session_id",
            "referring_tool",
            "state_fields",
            "declaration",
            "region",
            "matched_region",
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


class ExternalRegistrationSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    title = EnumField(required=False, enum=enums.PersonTitle)
    first_name = serializers.CharField(required=True, max_length=256)
    middle_name = serializers.CharField(required=False, max_length=256)
    last_name = serializers.CharField(required=True, max_length=256)
    suffix = serializers.CharField(required=False, max_length=256)

    date_of_birth = serializers.DateField(required=True, input_formats=["iso-8601"])

    email = serializers.EmailField(required=True, max_length=256)
    phone = PhoneNumberField(required=False)

    address1 = serializers.CharField(required=True, max_length=256)
    address2 = serializers.CharField(required=False, max_length=256)
    city = serializers.CharField(required=True, max_length=256)
    state = serializers.ChoiceField(
        choices=STATES,
        validators=[state_code_validator],
        required=True,
        source="state_id",
    )
    zipcode = serializers.CharField(validators=[zip_validator], required=True)

    sms_opt_in = RequiredBooleanField(
        required=True, validators=[must_be_true_validator]
    )
    sms_opt_in_subscriber = RequiredBooleanField(
        required=False, validators=[must_be_true_validator]
    )

    def validate(self, data):
        """
        To guarantee our ability to maintain backwards-compatibility, we reject
        extra fields -- we don't want someone to be passing, e.g., "previous_name"
        (which we would ignore), and then run into issues if we add a field with
        that name with different validation requirements than their assumptions.
        """
        if hasattr(self, "initial_data"):
            unknown_keys = set(self.initial_data.keys()) - set(self.fields.keys())
            if unknown_keys:
                raise ValidationError("Got unknown fields: {}".format(unknown_keys))

        if (
            data.get("state_id").lower() == "tn"
            and data.get("title") == enums.PersonTitle.MX
        ):
            raise ValidationError("Tennesee does not allow a title of Mx.")

        return data

    def create(self, validated_data):
        validated_data["action"] = Action.objects.create()
        validated_data["subscriber"] = self.request_subscriber(validated_data)
        validated_data["gender"] = self.guess_gender_from_title(validated_data)
        validated_data["status"] = enums.TurnoutActionStatus.INCOMPLETE
        return super().create(validated_data)

    def request_subscriber(self, data):
        return self.context.get("request").auth.subscriber

    def guess_gender_from_title(self, data):
        if data.get("title"):
            return data.get("title").guess_registration_gender()
        else:
            return None

    class Meta:
        model = Registration
        fields = (
            "title",
            "first_name",
            "middle_name",
            "last_name",
            "suffix",
            "date_of_birth",
            "email",
            "phone",
            "address1",
            "address2",
            "city",
            "state",
            "zipcode",
            "sms_opt_in",
            "sms_opt_in_subscriber",
            "subscriber",
            "gender",
            "status",
        )
