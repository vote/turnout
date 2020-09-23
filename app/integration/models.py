from django.db import models

from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel
from common.validators import zip_validator


class Link(UUIDModel, TimestampModel):
    action = models.ForeignKey("action.Action", null=True, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(
        "multi_tenant.Client", null=True, on_delete=models.CASCADE
    )
    external_tool = TurnoutEnumField(enums.ExternalToolType, null=True)
    external_id = models.TextField(null=True)

    class Meta:
        ordering = ["-created_at"]


class MoverLead(UUIDModel, TimestampModel):
    source_created_at = models.DateTimeField(null=True)
    first_name = models.TextField(null=True)
    last_name = models.TextField(null=True)
    email = models.EmailField(null=True)
    move_date = models.DateTimeField(null=True)

    new_address1 = models.TextField(null=True)
    new_address2 = models.TextField(null=True, blank=True)
    new_city = models.TextField(null=True)
    new_state = models.TextField(null=True)
    new_zipcode = models.TextField(null=True, validators=[zip_validator])
    new_zipcode_plus4 = models.TextField(null=True)
    new_housing_tenure = models.TextField(null=True)
    new_region = models.ForeignKey(
        "official.Region",
        null=True,
        on_delete=models.SET_NULL,
        related_name="moverlead_new",
    )

    old_address1 = models.TextField(null=True)
    old_address2 = models.TextField(null=True, blank=True)
    old_city = models.TextField(null=True)
    old_state = models.TextField(null=True)
    old_zipcode = models.TextField(null=True, validators=[zip_validator])
    old_zipcode_plus4 = models.TextField(null=True)
    old_housing_tenure = models.TextField(null=True)
    old_region = models.ForeignKey(
        "official.Region",
        null=True,
        on_delete=models.SET_NULL,
        related_name="moverlead_old",
    )

    actionnetwork_person_id = models.TextField(null=True)

    blank_register_forms_action = models.ForeignKey(
        "action.Action", on_delete=models.PROTECT, null=True, db_index=True
    )
    blank_register_forms_item = models.ForeignKey(
        "storage.StorageItem", null=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"MoverLead {self.first_name} {self.last_name}, {self.old_state} -> {self.new_state} ({self.uuid})"
