from rest_framework import serializers
from rest_framework.fields import empty


class RequiredBooleanField(serializers.BooleanField):
    # In order to require a True/False submission for a boolean, we need this code
    # From https://stackoverflow.com/a/55605007/1588398
    def get_value(self, dictionary):
        return dictionary.get(self.field_name, empty)
