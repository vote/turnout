import markdown
import reversion
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from enumfields import EnumField

from common import enums
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
    field_format = EnumField(
        enums.StateFieldFormats, null=True, default=enums.StateFieldFormats.MARKDOWN
    )

    class Meta(object):
        ordering = ["slug"]

    def __str__(self):
        return self.slug


class StateInformationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("field_type")


@reversion.register()
class StateInformation(UUIDModel, TimestampModel):
    state = models.ForeignKey("State", on_delete=models.CASCADE)
    field_type = models.ForeignKey(
        "StateInformationFieldType", on_delete=models.CASCADE
    )
    text = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    objects = StateInformationManager()

    class Meta(object):
        unique_together = ["state", "field_type"]
        ordering = ["field_type__slug", "state"]

    def __str__(self):
        return f"{self.state} -- {self.field_type}"

    def html(self):
        return markdown.markdown(self.text)


class UpdateNotificationWebhookManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .exclude(type__isnull=True)
            .exclude(trigger_url__isnull=True)
        )


class UpdateNotificationWebhook(UUIDModel, TimestampModel):
    name = models.TextField(null=True)
    type = EnumField(enums.NotificationWebhookTypes, null=True)
    trigger_url = models.URLField(null=True, max_length=200)
    last_triggered = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(null=True, default=True)

    objects = UpdateNotificationWebhookManager()

    def __str__(self):
        return self.name


@receiver(post_save, sender=StateInformationFieldType)
def process_new_information_field(sender, instance, **kwargs):
    if kwargs["created"]:
        for state in State.objects.all():
            with reversion.create_revision():
                StateInformation(state=state, field_type=instance).save()
