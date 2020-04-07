from django.db import models
from enumfields import EnumField

from common import enums
from common.utils.models import TimestampModel, UUIDModel


class Event(UUIDModel, TimestampModel):
    action = models.ForeignKey("action.Action", on_delete=models.PROTECT, db_index=True)
    event_type = EnumField(enums.EventType, max_length=100)

    class Meta:
        ordering = ["-created_at"]
