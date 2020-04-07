from enumfields.drf.serializers import EnumSupportSerializerMixin
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from action.mixin_serializers import ActionSerializerMixin
from common.validators import state_code_validator
from election.choices import STATES
from multi_tenant.mixins_serializers import PartnerSerializerMixin

from .models import Lookup, zip_validator


class LookupSerializer(
    ActionSerializerMixin,
    PartnerSerializerMixin,
    EnumSupportSerializerMixin,
    serializers.ModelSerializer,
):
    phone = PhoneNumberField(required=False)
    zipcode = serializers.CharField(validators=[zip_validator])
    state = serializers.ChoiceField(
        choices=STATES, required=True, validators=[state_code_validator]
    )

    class Meta:
        model = Lookup
        fields = (
            "partner",
            "first_name",
            "last_name",
            "address1",
            "address2",
            "city",
            "zipcode",
            "age",
            "state",
            "phone",
            "email",
            "sms_opt_in",
            "date_of_birth",
            "too_many",
            "registered",
            "response",
            "utm_campaign",
            "utm_source",
            "utm_medium",
            "source",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True},
            "date_of_birth": {"required": True},
            "address1": {"required": True},
            "city": {"required": True},
            "too_many": {"read_only": True},
            "registered": {"read_only": True},
            "response": {"read_only": True},
        }
