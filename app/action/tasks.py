from celery import shared_task
from django.conf import settings

from action.models import Action
from common.enums import EventType
from common.i90 import shorten_url
from event_tracking.models import Event
from integration.tasks import sync_action_to_actionnetwork
from smsbot.tasks import _send_welcome_sms, send_welcome_sms
from voter.tasks import voter_lookup_action


@shared_task
def action_finish(action_pk: str) -> None:
    action = Action.objects.get(pk=action_pk)
    item = action.get_source_item()

    if settings.ACTIONNETWORK_SYNC:
        sync_action_to_actionnetwork.delay(action_pk)

    if settings.SMS_POST_SIGNUP_ALERT and item.phone:
        if "BallotRequest" in str(type(item)):
            tool = "absentee"
        elif "Registration" in str(type(item)):
            tool = "register"
        elif "Lookup" in str(type(item)):
            tool = "verifier"
        elif "ReminderRequest" in str(type(item)):
            tool = "reminder"
        else:
            tool = None
        send_welcome_sms.apply_async(
            args=(str(item.phone), tool), countdown=settings.SMS_OPTIN_REMINDER_DELAY,
        )

    voter_lookup_action(action_pk)


@shared_task
def action_check_unfinished(action_pk: str) -> None:
    action = Action.objects.get(pk=action_pk)

    if Event.objects.filter(
        action=action,
        event_type__in=[
            EventType.FINISH_SELF_PRINT,
            EventType.FINISH_EXTERNAL,
            EventType.FINISH_LOB,
            EventType.FINISH_LEO,
            EventType.FINISH,
        ],
    ).exists():
        return

    # they didn't finish the tool
    if settings.ACTIONNETWORK_SYNC:
        sync_action_to_actionnetwork.delay(action_pk)

    item = action.get_source_item()
    if item.phone:
        n = _send_welcome_sms(str(item.phone))
        if not n:
            return

        query_params = item.get_query_params()
        if "BallotRequest" in str(type(item)):
            what = "requesting your absentee ballot"
            url = f"{settings.WWW_ORIGIN}/vote-by-mail/?{query_params}"
        elif "Registration" in str(type(item)):
            what = "registering to vote"
            url = f"{settings.WWW_ORIGIN}/register-to-vote/?{query_params}"
        else:
            return
        n.send_sms(
            f"It looks like you didn't finish {what}. To continue the process, please visit {shorten_url(url)}"
        )

    voter_lookup_action(action_pk)