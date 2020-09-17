from uuid import UUID

from django.conf import settings

from common import enums
from election.models import StateInformation
from event_tracking.models import Event

from .models import Registration
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

    registration = Registration.objects.get(action_id=action_id)

    # no upsell in vbm_universal states
    if StateInformation.objects.filter(
        state=registration.state, field_type__slug="vbm_universal", text="True",
    ).exists():
        return

    external_tool_upsell.apply_async(
        (registration.uuid,), countdown=settings.REGISTER_UPSELL_DELAY_SECONDS
    )


register_hooks = {
    enums.EventType.FINISH_EXTERNAL: finish_external,
}
