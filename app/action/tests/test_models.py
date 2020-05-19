import pytest
from model_bakery import baker

from common import enums
from event_tracking.models import Event

from action.models import ActionDetails


@pytest.mark.django_db
def test_create_event():
    action = baker.make_recipe("action.action")
    action.track_event(enums.EventType.FINISH_EXTERNAL)

    assert Event.objects.filter(action=action).count() == 1
    event = Event.objects.filter(action=action).first()
    assert event.event_type == enums.EventType.FINISH_EXTERNAL


@pytest.mark.django_db
def test_finished_generic():
    action = baker.make_recipe("action.action")
    action.track_event(enums.EventType.FINISH)

    assert ActionDetails.objects.count() == 1
    actiondetail = ActionDetails.objects.get(action=action)

    assert actiondetail.finished == True
    assert actiondetail.self_print == False
    assert actiondetail.finished_external_service == False
    assert actiondetail.leo_message_sent == False
    assert actiondetail.total_downloads == None


@pytest.mark.django_db
def test_finished_self_print():
    action = baker.make_recipe("action.action")
    action.track_event(enums.EventType.FINISH_SELF_PRINT)

    assert ActionDetails.objects.count() == 1
    actiondetail = ActionDetails.objects.get(action=action)

    assert actiondetail.finished == False
    assert actiondetail.self_print == True
    assert actiondetail.finished_external_service == False
    assert actiondetail.leo_message_sent == False
    assert actiondetail.total_downloads == 0


@pytest.mark.django_db
def test_finished_external_visit():
    action = baker.make_recipe("action.action")
    action.track_event(enums.EventType.FINISH_EXTERNAL)

    assert ActionDetails.objects.count() == 1
    actiondetail = ActionDetails.objects.get(action=action)

    assert actiondetail.finished == True
    assert actiondetail.self_print == False
    assert actiondetail.finished_external_service == True
    assert actiondetail.leo_message_sent == False
    assert actiondetail.total_downloads == None


@pytest.mark.django_db
def test_finished_leo_submission():
    action = baker.make_recipe("action.action")
    action.track_event(enums.EventType.FINISH_LEO)

    assert ActionDetails.objects.count() == 1
    actiondetail = ActionDetails.objects.get(action=action)

    assert actiondetail.finished == True
    assert actiondetail.self_print == False
    assert actiondetail.finished_external_service == False
    assert actiondetail.leo_message_sent == True
    assert actiondetail.total_downloads == None


@pytest.mark.django_db
def test_finished_download():
    action = baker.make_recipe("action.action")
    action.track_event(enums.EventType.FINISH_SELF_PRINT)
    action.track_event(enums.EventType.DOWNLOAD)
    action.track_event(enums.EventType.DOWNLOAD)

    assert ActionDetails.objects.count() == 1
    actiondetail = ActionDetails.objects.get(action=action)

    assert actiondetail.finished == True
    assert actiondetail.self_print == True
    assert actiondetail.finished_external_service == False
    assert actiondetail.leo_message_sent == False
    assert actiondetail.total_downloads == 2
