from django.contrib.postgres.fields import JSONField
from django.core.validators import RegexValidator
from django.db import models
from enumfields import EnumField
from phonenumber_field.modelfields import PhoneNumberField

from common.utils.models import TimestampModel, UUIDModel

zip_validator = RegexValidator(r"^[0-9]{5}$", "Zip codes are 5 digits")


class Lookup(UUIDModel, TimestampModel):
    person = models.ForeignKey("people.Person", null=True, on_delete=models.PROTECT)



    first_name = models.TextField()
    last_name = models.TextField()
    state = models.ForeignKey("election.State", on_delete=models.PROTECT)
    registered = models.BooleanField(null=True)
    too_many = models.BooleanField(null=True)
    response = JSONField()

    date_of_birth = models.DateField(null=True, blank=True)
    unparsed_full_address = models.TextField(null=True, blank=True)
    street_number = models.TextField(null=True, blank=True)
    street_name = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    zipcode = models.TextField(null=True, blank=True, validators=[zip_validator])
    age = models.IntegerField(null=True, blank=True)
    phone = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    class Meta(object):
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.state.pk}".strip()
