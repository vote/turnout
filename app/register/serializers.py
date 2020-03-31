import collections
import logging

from enumfields.drf.serializers import EnumSupportSerializerMixin
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework.fields import empty

from common.utils.fields import RequiredBooleanField
from common.validators import state_code_validator, zip_validator
from election.choices import STATES
from multi_tenant.mixins_serializers import PartnerSerializerMixin

from .models import Registration

logger = logging.getLogger("register")


MINIMUM_NECESSARY_FIELDS = [
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
NATIONALLY_REQUIRED_FIELDS = ["state_id_number", "us_citizen", "is_18_or_over"]
OPTIONAL_FIELDS = [
    "partner",
    "suffix",
    "phone",
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
]


class RegistrationSerializer(
    PartnerSerializerMixin, EnumSupportSerializerMixin, serializers.ModelSerializer
):
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
    is_18_or_over = RequiredBooleanField(required=False)
    us_citizen = RequiredBooleanField(required=False)

    class Meta:
        model = Registration
        fields = MINIMUM_NECESSARY_FIELDS + NATIONALLY_REQUIRED_FIELDS + OPTIONAL_FIELDS

    def __init__(self, instance=None, data=empty, **kwargs):
        self.incomplete = kwargs.pop("incomplete", False)
        super().__init__(instance=instance, data=data, **kwargs)

    def get_fields(self):
        initial_fields = super().get_fields()
        fields = collections.OrderedDict()
        for key, value in initial_fields.items():
            if key in MINIMUM_NECESSARY_FIELDS:
                value.required = True
            elif not self.incomplete and key in NATIONALLY_REQUIRED_FIELDS:
                value.required = True
            else:
                value.required = False
            fields[key] = value
        return fields
