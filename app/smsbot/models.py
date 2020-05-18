from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from common.enums import MessageDirectionType
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel


class Number(UUIDModel, TimestampModel):
    phone = PhoneNumberField(null=True, db_index=True)

    welcome_time = models.DateTimeField(null=True, blank=True)
    opt_out_time = models.DateTimeField(null=True, blank=True)
    opt_in_time = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        ordering = ["-created_at"]

    def __str__(self):
        return f"Number - {self.phone}"


class SMSMessage(UUIDModel, TimestampModel):
    phone = PhoneNumberField(null=True, db_index=True)
    direction = TurnoutEnumField(MessageDirectionType)
    message = models.TextField(blank=True, null=True)

    class Meta(object):
        ordering = ["-created_at"]

    def __str__(self):
        return f"SMSMessage - {self.phone} {self.direction}"
