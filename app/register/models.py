from django.contrib.postgres.fields import JSONField
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from action.mixin_models import ActionModel
from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import (
    SearchableModel,
    TimestampModel,
    TrackingModel,
    UUIDModel,
)
from common.validators import zip_validator
from multi_tenant.mixins_models import SubscriberModel


class Registration(
    ActionModel,
    SubscriberModel,
    TrackingModel,
    SearchableModel("email", "last_name", "first_name"),  # type: ignore
    UUIDModel,
    TimestampModel,
):
    title = TurnoutEnumField(enums.PersonTitle, null=True)
    first_name = models.TextField(null=True)
    middle_name = models.TextField(null=True)
    last_name = models.TextField(null=True)
    suffix = models.TextField(null=True)
    date_of_birth = models.DateField(null=True)
    email = models.EmailField(null=True)
    phone = PhoneNumberField(null=True, db_index=True)
    address1 = models.TextField(null=True)
    address2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True)
    state = models.ForeignKey(
        "election.State",
        on_delete=models.PROTECT,
        related_name="registration_primary",
        null=True,
    )
    zipcode = models.TextField(null=True, validators=[zip_validator])
    deliverable = models.BooleanField(null=True)

    previous_title = TurnoutEnumField(enums.PersonTitle, null=True, blank=True)
    previous_first_name = models.TextField(null=True, blank=True)
    previous_middle_name = models.TextField(null=True, blank=True)
    previous_last_name = models.TextField(null=True, blank=True)
    previous_suffix = models.TextField(null=True, blank=True)

    previous_address1 = models.TextField(null=True, blank=True)
    previous_address2 = models.TextField(null=True, blank=True)
    previous_city = models.TextField(null=True, blank=True)
    previous_state = models.ForeignKey(
        "election.State",
        on_delete=models.PROTECT,
        related_name="registration_previous",
        null=True,
    )
    previous_zipcode = models.TextField(
        null=True, validators=[zip_validator], blank=True
    )

    mailing_address1 = models.TextField(null=True, blank=True)
    mailing_address2 = models.TextField(null=True, blank=True)
    mailing_city = models.TextField(null=True, blank=True)
    mailing_state = models.ForeignKey(
        "election.State",
        on_delete=models.PROTECT,
        related_name="registration_mailing",
        null=True,
    )
    mailing_zipcode = models.TextField(
        null=True, validators=[zip_validator], blank=True
    )
    mailing_deliverable = models.BooleanField(null=True)

    request_mailing_address1 = models.TextField(null=True, blank=True)
    request_mailing_address2 = models.TextField(null=True, blank=True)
    request_mailing_city = models.TextField(null=True, blank=True)
    request_mailing_state = models.ForeignKey(
        "election.State",
        on_delete=models.PROTECT,
        related_name="registration_request_mailing",
        null=True,
    )
    request_mailing_zipcode = models.TextField(
        null=True, validators=[zip_validator], blank=True
    )
    request_mailing_deliverable = models.BooleanField(null=True)

    gender = TurnoutEnumField(enums.RegistrationGender, null=True)
    race_ethnicity = TurnoutEnumField(enums.RaceEthnicity, null=True)
    party = TurnoutEnumField(enums.PoliticalParties, null=True)

    us_citizen = models.BooleanField(null=True, default=False)
    sms_opt_in = models.BooleanField(null=True, blank=True, default=None)

    status = TurnoutEnumField(
        enums.TurnoutActionStatus, default=enums.TurnoutActionStatus.PENDING, null=True,
    )

    result_item = models.ForeignKey(
        "storage.StorageItem", null=True, on_delete=models.SET_NULL
    )
    result_item_mail = models.ForeignKey(
        "storage.StorageItem",
        null=True,
        on_delete=models.SET_NULL,
        related_name="registration_mail",
    )

    referring_tool = TurnoutEnumField(enums.ToolName, null=True, blank=True)

    state_fields = JSONField(null=True, blank=True)
    state_api_result = JSONField(null=True, blank=True)

    custom_ovr_link = models.TextField(null=True, blank=True)

    matched_region = models.ForeignKey(
        "official.Region", null=True, on_delete=models.SET_NULL, related_name="+"
    )
    region = models.ForeignKey(
        "official.Region", null=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Registration - {self.first_name} {self.last_name}, {self.state.pk}".strip()

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
