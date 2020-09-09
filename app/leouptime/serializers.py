from rest_framework import serializers

from .models import Site, SiteCheck, SiteDowntime


class SiteCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteCheck
        fields = [
            "uuid",
            "site",
            "state_up",
            "blocked",
            "ignore",
            "load_time",
            "error",
            "proxy",
            "created_at",
            "title",
            "content",
        ]


class SiteSerializer(serializers.ModelSerializer):
    last_went_down_check = SiteCheckSerializer(read_only=True)
    last_went_up_check = SiteCheckSerializer(read_only=True)

    class Meta:
        model = Site
        fields = [
            "uuid",
            "url",
            "description",
            "state_up",
            "state_changed_at",
            "last_went_down_check",
            "last_went_up_check",
            "last_went_blocked_check",
            "last_went_unblocked_check",
            "last_tweet_at",
            "uptime_day",
            "uptime_week",
            "uptime_month",
            "uptime_quarter",
        ]


class SiteDowntimeSerializer(serializers.ModelSerializer):
    site = SiteSerializer(read_only=True)
    down_check = SiteCheckSerializer(read_only=True)
    up_check = SiteCheckSerializer(read_only=True)
    duration = serializers.SerializerMethodField("get_duration")

    def get_duration(self, obj):
        if obj.up_check and obj.down_check:
            return (obj.up_check.created_at - obj.down_check.created_at).total_seconds()
        else:
            return None

    class Meta:
        model = SiteDowntime
        fields = [
            "uuid",
            "site",
            "down_check",
            "up_check",
            "duration",
        ]
