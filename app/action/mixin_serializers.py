from typing import TYPE_CHECKING, Any, Dict

from rest_framework import serializers

from .models import Action

if TYPE_CHECKING:
    _Base = serializers.ModelSerializer
else:
    _Base = object


class ActionSerializerMixin(_Base):
    action = serializers.PrimaryKeyRelatedField(read_only=True, required=False)

    def create(self, validated_data: Dict[(str, Any)]) -> Dict[(str, Any)]:
        validated_data["action"] = Action.objects.create()
        return super().create(validated_data)
