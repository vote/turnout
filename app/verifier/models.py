from django.contrib.postgres.fields import JSONField
from django.db import models
from enumfields import EnumField
from phonenumber_field.modelfields import PhoneNumberField

from action.mixin_models import ActionModel
from common import enums
from common.utils.models import TimestampModel, TrackingModel, UUIDModel
from common.validators import zip_validator
from multi_tenant.mixins_models import PartnerModel


class Lookup(ActionModel, PartnerModel, TrackingModel, UUIDModel, TimestampModel):
    person = models.ForeignKey("people.Person", null=True, on_delete=models.PROTECT)

    first_name = models.TextField()
    last_name = models.TextField()
    state = models.ForeignKey("election.State", on_delete=models.PROTECT)
    registered = models.BooleanField(null=True)
    voter_status = EnumField(enums.VoterStatus, null=True)
    too_many = models.BooleanField(null=True)
    response = JSONField()

    date_of_birth = models.DateField(null=True, blank=True)
    unparsed_full_address = models.TextField(null=True, blank=True)
    address1 = models.TextField(null=True, blank=True)
    address2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    zipcode = models.TextField(null=True, blank=True, validators=[zip_validator])
    age = models.IntegerField(null=True, blank=True)
    gender = EnumField(enums.TargetSmartGender, null=True)
    phone = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    sms_opt_in = models.BooleanField(null=True, blank=True, default=None)

    class Meta(object):
        ordering = ["-created_at"]

    def __str__(self):
        return f"Verification - {self.first_name} {self.last_name}, {self.state.pk}".strip()
