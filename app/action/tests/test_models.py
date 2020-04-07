import pytest
from model_bakery import baker

from common import enums
from event_tracking.models import Event


@pytest.mark.django_db
def test_create_event():
    action = baker.make_recipe("action.action")
    action.track_event(enums.EventType.OFFICIAL_TOOL_VISIT)

    assert Event.objects.filter(action=action).count() == 1
    event = Event.objects.filter(action=action).first()
    assert event.event_type == enums.EventType.OFFICIAL_TOOL_VISIT
