from enumfields.drf.serializers import EnumSupportSerializerMixin
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from election.choices import STATES
from election.models import state_code_validator

from .models import Lookup, zip_validator


class LookupSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    phone = PhoneNumberField(required=False)
    zipcode = serializers.CharField(validators=[zip_validator])
    state = serializers.ChoiceField(
        choices=STATES, required=True, validators=[state_code_validator]
    )

    class Meta:
        model = Lookup
        fields = (
            "first_name",
            "last_name",
            "street_number",
            "street_name",
            "unparsed_full_address",
            "city",
            "zipcode",
            "age",
            "state",
            "phone",
            "email",
            "date_of_birth",
            "too_many",
            "registered",
            "response",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True},
            "date_of_birth": {"required": True},
            "too_many": {"read_only": True},
            "registered": {"read_only": True},
            "response": {"read_only": True},
        }
