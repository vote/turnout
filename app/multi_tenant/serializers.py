from rest_framework import serializers

from .models import PartnerSlug


class PartnerSlugSerializer(serializers.ModelSerializer):
    partner = serializers.SlugRelatedField(read_only=True, slug_field="name")

    class Meta:
        model = PartnerSlug
        fields = ["partner"]
