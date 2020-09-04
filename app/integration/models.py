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


class MymoveLead(UUIDModel, TimestampModel):
    mymove_created_at = models.DateTimeField(null=True)
    first_name = models.TextField(null=True)
    last_name = models.TextField(null=True)
    email = models.EmailField(null=True)
    move_date = models.DateTimeField(null=True)

    new_address1 = models.TextField(null=True)
    new_address2 = models.TextField(null=True, blank=True)
    new_city = models.TextField(null=True)
    new_state = models.ForeignKey(
        "election.State",
        on_delete=models.PROTECT,
        related_name="mymove_lead_new",
        null=True,
    )
    new_zipcode = models.TextField(null=True, validators=[zip_validator])
    new_zipcode_plus4 = models.TextField(null=True)
    new_housing_tenure = models.TextField(null=True)

    old_address1 = models.TextField(null=True)
    old_address2 = models.TextField(null=True, blank=True)
    old_city = models.TextField(null=True)
    old_state = models.ForeignKey(
        "election.State",
        on_delete=models.PROTECT,
        related_name="mymove_lead_old",
        null=True,
    )
    old_zipcode = models.TextField(null=True, validators=[zip_validator])
    old_zipcode_plus4 = models.TextField(null=True)
    old_housing_tenure = models.TextField(null=True)

    actionnetwork_person_id = models.TextField(null=True)

    class Meta:
        ordering = ["-created_at"]
