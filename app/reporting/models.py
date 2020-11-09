from django.db import models

from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel
from multi_tenant.mixins_models import SubscriberModel


class Report(SubscriberModel, UUIDModel, TimestampModel):
    author = models.ForeignKey("accounts.User", null=True, on_delete=models.PROTECT)
    status = TurnoutEnumField(
        enums.ReportStatus, null=True, default=enums.ReportStatus.PENDING
    )
    type = TurnoutEnumField(enums.ReportType, null=True)
    result_item = models.ForeignKey(
        "storage.StorageItem", null=True, on_delete=models.SET_NULL, blank=True
    )


class SubscriberStats(SubscriberModel, UUIDModel):
    tool = TurnoutEnumField(enums.ToolName)
    count = models.BigIntegerField()

    class Meta:
        unique_together = (("subscriber", "tool"),)


class StatsRefresh(models.Model):
    last_run = models.DateTimeField(primary_key=True)
