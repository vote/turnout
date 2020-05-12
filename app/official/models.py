from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from common.utils.models import TimestampModel
from common.validators import zip_validator


class USVFModel(TimestampModel):
    external_id = models.IntegerField(primary_key=True)
    external_updated = models.DateTimeField(null=True)

    class Meta:
        abstract = True


class Region(USVFModel):
    name = models.TextField(null=True)
    municipality = models.TextField(null=True, db_index=True)
    municipality_type = models.TextField(null=True)
    county = models.TextField(null=True, db_index=True)
    state = models.ForeignKey("election.State", null=True, on_delete=models.PROTECT)

    class Meta:
        ordering = ["external_id"]

    def __str__(self):
        return self.name


class Office(USVFModel):
    region = models.ForeignKey(Region, null=True, on_delete=models.CASCADE)
    hours = models.TextField(null=True)
    notes = models.TextField(null=True)

    class Meta:
        ordering = ["external_id"]


class Address(USVFModel):
    office = models.ForeignKey(Office, null=True, on_delete=models.CASCADE)
    address = models.TextField(null=True)
    address2 = models.TextField(null=True)
    address3 = models.TextField(null=True)
    city = models.TextField(null=True)
    state = models.ForeignKey("election.State", null=True, on_delete=models.PROTECT)
    zipcode = models.TextField(null=True, validators=[zip_validator])

    website = models.URLField(null=True)
    email = models.EmailField(null=True)
    phone = PhoneNumberField(null=True)
    fax = PhoneNumberField(null=True)

    is_physical = models.BooleanField(default=False, null=True)
    is_regular_mail = models.BooleanField(default=False, null=True)

    process_domestic_registrations = models.BooleanField(default=False, null=True)
    process_absentee_requests = models.BooleanField(default=False, null=True)
    process_absentee_ballots = models.BooleanField(default=False, null=True)
    process_overseas_requests = models.BooleanField(default=False, null=True)
    process_overseas_ballots = models.BooleanField(default=False, null=True)

    class Meta:
        ordering = ["external_id"]

    @property
    def full_address(self):
        city = self.city.title() if self.city else ""
        state = self.state.code if self.state else ""

        return "\n".join(
            [
                line
                for line in [
                    self.address,
                    self.address2,
                    self.address3,
                    f"{city}, {state} {self.zipcode}",
                ]
                if line is not None and len(line) > 0
            ]
        )
