from django.db import models
from enumfields import Enum
from phonenumber_field.modelfields import PhoneNumberField

from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel


class PhoneType(Enum):
    MOBILE = "m"
    LANDLINE = "l"
    FAX = "f"


class PersonRelationshipModel(UUIDModel, TimestampModel):
    person = models.ForeignKey("people.Person", on_delete=models.CASCADE)

    class Meta(object):
        abstract = True


class Person(UUIDModel, TimestampModel):
    date_of_birth = models.DateField(null=True)
    us_citizen = models.BooleanField(default=True)
    phone_numbers = models.ManyToManyField(
        "people.Phone", through="people.PhoneRelationships"
    )
    addresses = models.ManyToManyField(
        "people.Address", through="people.AddressRelationships"
    )
    emails = models.ManyToManyField("people.Email", through="people.EmailRelationships")


class Name(UUIDModel, TimestampModel):
    person = models.ForeignKey(
        "people.Person", related_name="names", null=True, on_delete=models.SET_NULL
    )
    primary = models.BooleanField(default=True, db_index=True)
    title = models.TextField(blank=True, null=True)
    first_name = models.TextField(blank=True, null=True)
    last_name = models.TextField(blank=True, null=True)
    suffix = models.TextField(blank=True, null=True)


class EmailRelationships(PersonRelationshipModel):
    email = models.ForeignKey("people.Email", on_delete=models.CASCADE)
    primary = models.BooleanField(default=True, db_index=True)


class Email(UUIDModel, TimestampModel):
    email = models.EmailField(max_length=150)


class PhoneRelationships(PersonRelationshipModel):
    phone = models.ForeignKey("people.Phone", on_delete=models.CASCADE)
    active = models.BooleanField(default=True)


class Phone(UUIDModel, TimestampModel):
    phone_type = TurnoutEnumField(PhoneType, db_index=True)
    phone_number = PhoneNumberField()


class AddressRelationships(PersonRelationshipModel):
    address = models.ForeignKey("people.Address", on_delete=models.CASCADE)
    current_mailing = models.BooleanField(default=False, db_index=True)
    current_physical = models.BooleanField(default=False, db_index=True)


class Address(UUIDModel, TimestampModel):
    state = models.ForeignKey(
        "election.State", related_name="person_addresses", on_delete=models.PROTECT
    )
    current = models.BooleanField(default=True, db_index=True)
    address1 = models.TextField(blank=True, null=True)
    address2 = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    zipcode = models.TextField(blank=True, null=True)
