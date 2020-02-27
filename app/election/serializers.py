from rest_framework import serializers

from common.enums import StateFieldFormats

from .models import State, StateInformation, StateInformationFieldType


class StateInfoSerializer(serializers.ModelSerializer):
    field_type = serializers.SlugRelatedField(read_only=True, slug_field="slug")

    class Meta:
        model = StateInformation
        fields = ("text", "field_type", "modified_at")

    def to_representation(self, instance):
        result = super().to_representation(instance)
        if instance.field_type.field_format == StateFieldFormats.BOOLEAN:
            result["value"] = instance.text.lower() == "true"
        return result


class StateSerializer(serializers.ModelSerializer):
    state_information = StateInfoSerializer(source="stateinformation_set", many=True)

    class Meta:
        model = State
        fields = (
            "code",
            "name",
            "state_information",
        )


class StateFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = StateInformationFieldType
        fields = ("slug", "long_name")
