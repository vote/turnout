from django.db import models

from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel


class Event(UUIDModel, TimestampModel):
    action = models.ForeignKey("action.Action", on_delete=models.PROTECT, db_index=True)
    event_type = TurnoutEnumField(enums.EventType)

    class Meta:
        ordering = ["-created_at"]
