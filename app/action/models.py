from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from absentee.models import BallotRequest
from common.utils.models import TimestampModel, UUIDModel
from event_tracking.models import Event
from integration.models import MymoveLead
from register.models import Registration
from reminder.models import ReminderRequest
from verifier.models import Lookup


class Action(UUIDModel, TimestampModel):
    voter = models.ForeignKey("voter.Voter", null=True, on_delete=models.SET_NULL)
    last_voter_lookup = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def track_event(self, event_type: Any) -> Event:
        return Event.objects.create(action=self, event_type=event_type)

    def get_source_item(self):
        for cls in BallotRequest, Registration, ReminderRequest, Lookup:
            try:
                return cls.objects.get(action=self)
            except ObjectDoesNotExist:
                pass
        try:
            return MymoveLead.objects.get(blank_register_forms_action=self)
        except ObjectDoesNotExist:
            pass
        return None


class ActionDetails(models.Model):
    action = models.OneToOneField(
        "action.Action",
        on_delete=models.DO_NOTHING,
        primary_key=True,
        related_name="details",
    )
    finished = models.BooleanField()
    self_print = models.BooleanField(null=True, db_column="self_print")
    finished_external_service = models.BooleanField(
        null=True, db_column="finish_external"
    )
    leo_message_sent = models.BooleanField(null=True, db_column="finish_leo")
    total_downloads = models.IntegerField(null=True, db_column="download_count")
    latest_event = models.DateTimeField(null=True, db_column="latest_event")

    class Meta:
        managed = False
