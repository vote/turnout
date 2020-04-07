from enumfields.drf.fields import EnumField
from enumfields.drf.serializers import EnumSupportSerializerMixin
from rest_framework import serializers

from action.models import Action
from common import enums
from common.validators import (
    must_be_true_validator,
    state_code_validator,
    zip_validator,
)

from .models import Event


class EventSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    action = serializers.PrimaryKeyRelatedField(queryset=Action.objects.all())
    event_type = EnumField(enum=enums.EventType)

    class Meta:
        model = Event
        fields = ["event_type", "action"]
