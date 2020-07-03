from django.db import models

from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel


class Link(UUIDModel, TimestampModel):
    action = models.ForeignKey("action.Action", null=True, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(
        "multi_tenant.Client", null=True, on_delete=models.CASCADE
    )
    external_tool = TurnoutEnumField(enums.ExternalToolType, null=True)
    external_id = models.TextField(null=True)

    class Meta:
        ordering = ["-created_at"]


class ExternalStateSite(UUIDModel, TimestampModel):
    name = models.TextField(null=True)
    description = models.TextField(null=True)
    state_up = models.BooleanField(null=True)
    state_changed_at = models.DateTimeField(null=True)
    last_tweet_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-modified_at"]
