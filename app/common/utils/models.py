from django.db import models
from django_smalluuid.models import SmallUUIDField, uuid_default


class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta(object):
        abstract = True


class UUIDModel(models.Model):
    uuid = SmallUUIDField(default=uuid_default(), editable=False, primary_key=True)

    class Meta(object):
        abstract = True


class TrackingModel(models.Model):
    utm_campaign = models.TextField(null=True, blank=True)
    utm_source = models.TextField(null=True, blank=True)
    utm_medium = models.TextField(null=True, blank=True)
    source = models.TextField(null=True, blank=True)

    class Meta(object):
        abstract = True
