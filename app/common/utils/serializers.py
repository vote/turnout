from urllib.parse import urlparse

from rest_framework import serializers

from .fields import SmallUUIDField


class SmallUUIDKeySerializer(serializers.Serializer):
    id = SmallUUIDField()


class TrackingSerializer(object):
    def validate_embed_url(self, value):
        parsed = urlparse(value)
        if not parsed.netloc:
            return value
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
