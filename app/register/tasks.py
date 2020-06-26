from celery import shared_task
from django.conf import settings

from common.analytics import statsd
from common.enums import EventType, TurnoutActionStatus
from integration.tasks import sync_registration_to_actionnetwork
from smsbot.tasks import send_welcome_sms


@shared_task
@statsd.timed("turnout.register.process_registration_submission")
def process_registration_submission(
    registration_pk: str, state_id_number: str, is_18_or_over: bool
) -> None:
    from .models import Registration
    from .generateform import process_registration

    registration = Registration.objects.select_related().get(pk=registration_pk)
    process_registration(registration, state_id_number, is_18_or_over)

    if registration.sms_opt_in and settings.SMS_POST_SIGNUP_ALERT:
        send_welcome_sms.apply_async(
            args=(str(registration.phone), "register"),
            countdown=settings.SMS_OPTIN_REMINDER_DELAY,
        )

    if settings.ACTIONNETWORK_SYNC:
        sync_registration_to_actionnetwork.delay(registration.uuid)


@shared_task
@statsd.timed("turnout.register.send_registration_notification")
def send_registration_notification(registration_pk: str) -> None:
    from .models import Registration
    from .notification import trigger_notification

    registration = Registration.objects.select_related().get(pk=registration_pk)
    registration.status = TurnoutActionStatus.PDF_SENT
    registration.save(update_fields=["status"])
    registration.action.track_event(EventType.FINISH_SELF_PRINT)

    trigger_notification(registration)
