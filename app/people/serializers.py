from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers


class OptInOutSerializer(serializers.Serializer):
    phone = PhoneNumberField(required=False)
    email = serializers.EmailField(required=False)
