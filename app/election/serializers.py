from rest_framework import serializers

from .models import State, StateInformation


class StateInfoSerializer(serializers.ModelSerializer):
    field_type = serializers.SlugRelatedField(read_only=True, slug_field="slug")

    class Meta:
        model = StateInformation
        fields = ("text", "field_type")


class StateSerializer(serializers.ModelSerializer):
    state_information = serializers.SerializerMethodField(
        method_name="stateinformation_flat"
    )

    def stateinformation_flat(self, obj):
        flat = {}
        for field in obj.stateinformation_set.select_related("field_type").all():
            flat[field.field_type.slug] = field.text
        return flat

    class Meta:
        model = State
        fields = (
            "code",
            "name",
            "state_information",
        )
