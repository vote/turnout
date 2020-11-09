from django.contrib.postgres.fields import JSONField
from django.db import models

from action.mixin_models import ActionModel
from common.utils.models import TimestampModel, TrackingModel, UUIDModel
from common.validators import zip_validator
from multi_tenant.mixins_models import SubscriberModel


class PollingPlaceLookup(
    ActionModel, SubscriberModel, TrackingModel, UUIDModel, TimestampModel,
):
    unstructured_address = models.TextField(null=True)
    dnc_result = JSONField(null=True)
    dnc_status = models.TextField(null=True)
    civic_result = JSONField(null=True)
    civic_status = models.TextField(null=True)

    state = models.ForeignKey("election.State", on_delete=models.PROTECT, null=True)
    address1 = models.TextField(null=True, blank=True)
    address2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    zipcode = models.TextField(null=True, blank=True, validators=[zip_validator])

    class Meta(object):
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Polling Place Lookup - {self.address1}, {self.city}, {self.state.pk} {self.zipcode}".strip()
