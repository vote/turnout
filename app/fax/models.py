from django.db import models
from django_smalluuid.models import SmallUUIDField, uuid_default
from phonenumber_field.modelfields import PhoneNumberField

from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel


class Fax(UUIDModel, TimestampModel):
    token = SmallUUIDField(default=uuid_default())
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
