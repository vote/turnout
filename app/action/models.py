from typing import Any

from django.db import models

from common.utils.models import TimestampModel, UUIDModel
from event_tracking.models import Event


class Action(UUIDModel, TimestampModel):
    class Meta:
        ordering = ["-created_at"]

    def track_event(self, event_type: Any) -> Event:
        return Event.objects.create(action=self, event_type=event_type)


class ActionDetails(models.Model):
    action = models.OneToOneField(
        "action.Action", on_delete=models.DO_NOTHING, primary_key=True
    )
    finished = models.BooleanField()
    self_print = models.BooleanField(null=True, db_column="self_print")
    finished_external_service = models.BooleanField(
        null=True, db_column="finish_external"
    )
    leo_message_sent = models.BooleanField(null=True, db_column="finish_leo")
    total_downloads = models.IntegerField(null=True, db_column="download_count")

    class Meta:
        managed = False
