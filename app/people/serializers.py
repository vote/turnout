from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from .models import NameOverride


class OptInOutSerializer(serializers.Serializer):
    phone = PhoneNumberField(required=False)
    email = serializers.EmailField(required=False)


class NameOverrideSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = NameOverride
        fields = [
            "email",
            "first_name",
            "last_name",
        ]
        minimum_necessary_fields = [
            "email",
            "first_name",
            "last_name",
        ]
