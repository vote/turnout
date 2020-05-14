from typing import TYPE_CHECKING, Any

from common.utils.models import TimestampModel, UUIDModel
from event_tracking.models import Event


class Action(UUIDModel, TimestampModel):
    class Meta:
        ordering = ["-created_at"]

    def track_event(self, event_type: Any) -> Event:
        return Event.objects.create(action=self, event_type=event_type)
