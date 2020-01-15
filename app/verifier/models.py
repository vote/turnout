from django.contrib.postgres.fields import JSONField
from django.core.validators import RegexValidator
from django.db import models
from enumfields import EnumField
from phonenumber_field.modelfields import PhoneNumberField

from common import enums
from common.utils.models import TimestampModel, UUIDModel

zip_validator = RegexValidator(r"^[0-9]{5}$", "Zip codes are 5 digits")


class Lookup(UUIDModel, TimestampModel):
    person = models.ForeignKey("people.Person", null=True, on_delete=models.PROTECT)

    first_name = models.TextField()
    last_name = models.TextField()
    state = models.ForeignKey("election.State", on_delete=models.PROTECT)
    registered = models.BooleanField(null=True)
    voter_status = EnumField(enums.VoterStatus, null=True)
    total_matches = models.IntegerField()
    response = JSONField()

    middle_name = models.TextField(null=True, blank=True)
    gender = EnumField(enums.CatalistGender, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address1 = models.TextField(null=True, blank=True)
    address2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    catalist_stateid = models.TextField(null=True, blank=True)
    zipcode = models.TextField(null=True, blank=True, validators=[zip_validator])
    county = models.TextField(null=True, blank=True)
    phone = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    distance = models.IntegerField(null=True, blank=True)

    class Meta(object):
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.state.pk}".strip()
