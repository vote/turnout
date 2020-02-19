import markdown
import reversion
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from common.utils.models import TimestampModel, UUIDModel

from .choices import STATES


def state_code_validator(code):
    """Validate states by code"""
    if code not in dict(STATES).keys():
        raise ValidationError(f"{code} is not a valid state code")


class State(TimestampModel):
    code = models.CharField(
        "Code",
        max_length=2,
        choices=[(x, x) for x, y in STATES],
        primary_key=True,
        editable=False,
    )
    name = models.CharField("Name", max_length=50)
    state_information = models.ManyToManyField(
        "StateInformationFieldType", through="StateInformation"
    )

    class Meta(object):
        ordering = ["code"]

    def __str__(self):
        return self.name


class StateInformationFieldType(UUIDModel, TimestampModel):
    slug = models.SlugField("Name", max_length=50, unique=True)
    long_name = models.CharField("Long Name", max_length=200)

    class Meta(object):
        ordering = ["slug"]

    def __str__(self):
        return self.slug


@reversion.register()
class StateInformation(UUIDModel, TimestampModel):
    state = models.ForeignKey("State", on_delete=models.CASCADE)
    field_type = models.ForeignKey(
        "StateInformationFieldType", on_delete=models.CASCADE
    )
    text = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta(object):
        unique_together = ["state", "field_type"]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.state} -- {self.field_type}"

    def html(self):
        return markdown.markdown(self.text)


@receiver(post_save, sender=StateInformationFieldType)
def process_new_information_field(sender, instance, **kwargs):
    if kwargs["created"]:
        for state in State.objects.all():
            with reversion.create_revision():
                StateInformation(state=state, field_type=instance).save()
