import datetime
from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from django.conf import settings

from action.models import Action
from event_tracking.models import Event
from common.enums import EventType


ABSENTEE_TEMPLATE = "fixed_absentee.html"
REGISTER_TEMPLATE = "fixed_register.html"


def email_fixed_links():
    for event in Event.objects.filter(
            event_type=EventType.FINISH_SELF_PRINT,
            created_at__gt=datetime.datetime(2020, 8, 24, 22, 46, 7, tzinfo=datetime.timezone.utc),
            created_at__lt=datetime.datetime(2020, 8, 25, 2, 58, 0, tzinfo=datetime.timezone.utc),
    ):
        action = event.action
        item = action.get_source_item()
        print(f"action {action} event {event} item {item}")

        if type(item) == "register.models.Registration":
            from register.notification import trigger_notification
            
            trigger_notification(item)
        elif type(item) == "absentee.models.BallotRequest":
            from absentee.notification import trigger_notification
            
            trigger_notification(item)
            
