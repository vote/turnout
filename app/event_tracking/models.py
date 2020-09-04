from django.db import models

from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel


class Event(UUIDModel, TimestampModel):
    action = models.ForeignKey("action.Action", on_delete=models.PROTECT, db_index=True)
    event_type = TurnoutEnumField(enums.EventType, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
        ]

    def check_hooks(self, tool):
        from absentee.event_hooks import absentee_hooks
        from register.event_hooks import register_hooks
        from verifier.event_hooks import verifier_hooks

        # Tool-specific hooks
        if tool == enums.ToolName.VERIFY.value:
            hook = verifier_hooks.get(self.event_type)
            if hook:
                hook(
                    self.action_id, self.uuid,
                )
        if tool == enums.ToolName.REGISTER.value:
            hook = register_hooks.get(self.event_type)
            if hook:
                hook(
                    self.action_id, self.uuid,
                )
        if tool == enums.ToolName.ABSENTEE.value:
            hook = absentee_hooks.get(self.event_type)
            if hook:
                hook(
                    self.action_id, self.uuid,
                )
