from rest_framework import serializers

from .fields import SmallUUIDField


class SmallUUIDKeySerializer(serializers.Serializer):
    id = SmallUUIDField()
