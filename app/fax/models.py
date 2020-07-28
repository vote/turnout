import uuid

from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel


class Fax(UUIDModel, TimestampModel):
    token = models.UUIDField(default=uuid.uuid4)
    storage_item = models.ForeignKey("storage.StorageItem", on_delete=models.PROTECT,)

    status = TurnoutEnumField(enums.FaxStatus)
    status_message = models.TextField(null=True)
    status_timestamp = models.DateTimeField(null=True)

    on_complete_task = models.TextField(null=True)
    on_complete_task_arg = models.TextField(null=True)

    to = PhoneNumberField(null=True)

    class Meta:
        ordering = ["-created_at"]

    def validate_token(self, token):
        return token == str(self.token)
