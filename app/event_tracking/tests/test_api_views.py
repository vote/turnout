import pytest
from rest_framework.test import APIClient

from common import enums
from event_tracking.models import Event
from register.api_views import RegistrationViewSet
from register.tests.test_api_views import REGISTER_API_ENDPOINT, VALID_REGISTRATION

TRACKING_API_ENDPOINT = "/v1/event/track/"


@pytest.mark.django_db
def test_register_object_created(mocker):
    mocker.patch.object(RegistrationViewSet, "task")
    client = APIClient()

    response = client.post(REGISTER_API_ENDPOINT, VALID_REGISTRATION)
    assert response.status_code == 200
    action_id = response.json()["action_id"]

    assert Event.objects.count() == 0
    response = client.post(
        TRACKING_API_ENDPOINT, {"action": action_id, "event_type": "FinishExternal"}
    )

    latest_event = Event.objects.first()
    assert str(latest_event.action.pk) == action_id
    assert latest_event.event_type == enums.EventType.FINISH_EXTERNAL
