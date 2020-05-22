from django.db import models

from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel
from multi_tenant.mixins_models import PartnerModel


class Report(PartnerModel, UUIDModel, TimestampModel):
    author = models.ForeignKey("accounts.User", null=True, on_delete=models.PROTECT)
    status = TurnoutEnumField(
        enums.ReportStatus, null=True, default=enums.ReportStatus.PENDING
    )
    type = TurnoutEnumField(enums.ReportType, null=True)
    result_item = models.ForeignKey(
        "storage.StorageItem", null=True, on_delete=models.SET_NULL, blank=True
    )
