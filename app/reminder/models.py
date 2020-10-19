from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from action.mixin_models import ActionModel
from common.utils.models import (
    SearchableModel,
    TimestampModel,
    TrackingModel,
    UUIDModel,
)
from common.validators import zip_validator
from multi_tenant.mixins_models import SubscriberModel


class ReminderRequest(
    ActionModel,
    SubscriberModel,
    TrackingModel,
    SearchableModel("email", "last_name", "first_name"),  # type: ignore
    UUIDModel,
    TimestampModel,
):
    first_name = models.TextField()
    last_name = models.TextField()
    state = models.ForeignKey("election.State", on_delete=models.PROTECT)
    date_of_birth = models.DateField(null=True, blank=True)
    address1 = models.TextField(null=True, blank=True)
    address2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    zipcode = models.TextField(null=True, blank=True, validators=[zip_validator])
    phone = PhoneNumberField(null=True, blank=True, db_index=True)
    email = models.EmailField(null=True, blank=True)
    sms_opt_in = models.BooleanField(null=True, blank=True, default=None)

    class Meta(object):
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reminder Request - {self.first_name} {self.last_name}, {self.state.pk}".strip()
