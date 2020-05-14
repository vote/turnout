import pytest
from model_bakery import baker

from common import enums
from event_tracking.models import Event
from register.tasks import send_registration_notification


@pytest.mark.django_db
def test_register_self_print_event_created(mocker):
    mocker.patch("register.notification.trigger_notification")
    registration = baker.make_recipe("register.registration")

    send_registration_notification(registration.pk)
    assert (
        Event.objects.filter(
            action=registration.action, event_type=enums.EventType.FINISH_SELF_PRINT
        ).count()
        == 1
    )
