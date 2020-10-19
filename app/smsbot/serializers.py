from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework.serializers import DateTimeField


class OptInOutSerializer(serializers.Serializer):
    phone = PhoneNumberField()
    time = DateTimeField(required=False)
