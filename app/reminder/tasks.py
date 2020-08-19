from celery import shared_task
from django.conf import settings

from common.analytics import statsd
from integration.tasks import sync_reminderrequest_to_actionnetwork
from smsbot.tasks import send_welcome_sms
from voter.tasks import voter_lookup_action


@shared_task
@statsd.timed("turnout.absentee.reminderrequest_followup")
def reminderrequest_followup(reminderrequest_pk: str) -> None:
    from .models import ReminderRequest

    reminder = ReminderRequest.objects.get(pk=reminderrequest_pk)

    voter_lookup_action.delay(reminder.action.pk)

    if settings.SMS_POST_SIGNUP_ALERT:
        send_welcome_sms.apply_async(
            args=(str(reminder.phone), "reminder"),
            countdown=settings.SMS_OPTIN_REMINDER_DELAY,
        )

    if settings.ACTIONNETWORK_SYNC:
        sync_reminderrequest_to_actionnetwork.delay(reminder.uuid)
