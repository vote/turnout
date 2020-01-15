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
    date_of_birth = serializers.DateField(required=False)

    class Meta:
        model = Lookup
        fields = (
            "first_name",
            "last_name",
            "middle_name",
            "gender",
            "date_of_birth",
            "address1",
            "address2",
            "city",
            "zipcode",
            "county",
            "state",
            "phone",
            "email",
            "registered",
            "voter_status",
            "total_matches",
            "response",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "registered": {"read_only": True},
            "voter_status": {"read_only": True},
            "total_matches": {"read_only": True},
            "response": {"read_only": True},
        }
