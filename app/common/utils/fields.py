from rest_framework import serializers
from rest_framework.fields import empty
from smalluuid import SmallUUID


class RequiredBooleanField(serializers.BooleanField):
    # In order to require a True/False submission for a boolean, we need this code
    # From https://stackoverflow.com/a/55605007/1588398
    def get_value(self, dictionary):
        return dictionary.get(self.field_name, empty)


class SmallUUIDField(serializers.CharField):
    def to_internal_value(self, data):
        if data == "" and self.allow_blank:
            return
        try:
            return SmallUUID(data)
        except ValueError:
            raise serializers.ValidationError("Not a valid SmallUUID")
