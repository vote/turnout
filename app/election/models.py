import datetime
from typing import Dict, Union

import markdown
import reversion
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.functional import cached_property

from cdn.utils import purge_cdn_tag, purge_cdn_tags
from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel

from .choices import STATES


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

    @cached_property
    def data(self) -> Dict[(str, Union[datetime.date, str, bool, None])]:
        data = {}
        for item in self.stateinformation_set.only(
            "field_type__slug", "text", "field_type__field_format"
        ):
            data[item.field_type.slug] = item.formal_format
        return data


class StateInformationFieldType(UUIDModel, TimestampModel):
    slug = models.SlugField("Name", max_length=50, unique=True)
    long_name = models.CharField("Long Name", max_length=200)
    field_format = TurnoutEnumField(
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

    @cached_property
    def formal_format(self) -> Union[datetime.date, str, bool, None]:
        content: Union[datetime.date, str, bool, None] = None
        if self.text == "":
            content = None
        elif self.field_type.field_format == enums.StateFieldFormats.BOOLEAN:
            content = self.text.lower() == "true"
        elif self.field_type.field_format == enums.StateFieldFormats.DATE:
            try:
                content = datetime.date.fromisoformat(self.text)
            except ValueError:
                content = None
        else:
            content = self.text
        return content


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
    type = TurnoutEnumField(enums.NotificationWebhookTypes, null=True)
    trigger_url = models.URLField(null=True, max_length=200)
    last_triggered = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(null=True, default=True)

    objects = UpdateNotificationWebhookManager()

    def __str__(self):
        return self.name


@receiver(post_save, sender=StateInformationFieldType)
def process_information_field(sender, instance, **kwargs):
    purge_cdn_tags(["state", "stateinformationfield", "stateinformationfieldtype"])
    if kwargs["created"]:
        for state in State.objects.all():
            with reversion.create_revision():
                StateInformation(state=state, field_type=instance).save()


@receiver(post_save, sender=StateInformation)
def process_state_information(sender, instance, **kwargs):
    if not kwargs["created"]:
        purge_cdn_tag(str(instance.state_id))
