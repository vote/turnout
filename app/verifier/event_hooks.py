from uuid import UUID

from django.conf import settings

from common import enums
from event_tracking.models import Event

from .models import Lookup
from .tasks import external_tool_upsell


def finish_external(action_id: UUID, event_id: UUID):
    # Make sure this is the first time this action has been reported to avoid
    # sending duplicate emails
    if (
        Event.objects.filter(
            action_id=action_id, event_type=enums.EventType.FINISH_EXTERNAL,
        )
        .exclude(uuid=event_id)
        .exists()
    ):
        return

    lookup = Lookup.objects.get(action_id=action_id)
    external_tool_upsell.apply_async(
        (lookup.uuid,), countdown=settings.VERIFIER_UPSELL_DELAY_SECONDS
    )


verifier_hooks = {enums.EventType.FINISH_EXTERNAL: finish_external}
