from typing import TYPE_CHECKING

from common.utils.models import TimestampModel, UUIDModel
from event_tracking.models import Event

if TYPE_CHECKING:
    from common import enums


class Action(UUIDModel, TimestampModel):
    class Meta:
        ordering = ["-created_at"]

    def track_event(self, event_type: "enums.EventType") -> Event:
        return Event.objects.create(action=self, event_type=event_type)
