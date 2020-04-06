from django.db import models
from enumfields import EnumField
from phonenumber_field.modelfields import PhoneNumberField

from common import enums
from common.utils.models import TimestampModel, TrackingModel, UUIDModel
from common.validators import zip_validator
from multi_tenant.mixins_models import PartnerModel


class Registration(PartnerModel, TrackingModel, UUIDModel, TimestampModel):
    title = EnumField(enums.PersonTitle, null=True)
    first_name = models.TextField(null=True)
    middle_name = models.TextField(null=True)
    last_name = models.TextField(null=True)
    suffix = models.TextField(null=True)
    date_of_birth = models.DateField(null=True)
    email = models.EmailField(null=True)
    phone = PhoneNumberField(null=True)
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

    previous_title = EnumField(enums.PersonTitle, null=True, blank=True)
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

    gender = EnumField(enums.RegistrationGender, null=True)
    race_ethnicity = EnumField(enums.RaceEthnicity, null=True)
    party = EnumField(enums.PoliticalParties, null=True)

    us_citizen = models.BooleanField(null=True, default=False)
    sms_opt_in = models.BooleanField(null=True, default=False)

    status = EnumField(
        enums.TurnoutRegistrationStatus,
        default=enums.TurnoutRegistrationStatus.PENDING,
        null=True,
    )

    result_item = models.ForeignKey(
        "storage.StorageItem", null=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Registration - {self.first_name} {self.last_name}, {self.state.pk}".strip()

    def get_fields(self):
        return [
            (field.verbose_name, field.value_from_object(self))
            for field in self.__class__._meta.fields
        ]
