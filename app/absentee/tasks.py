import logging

import sentry_sdk
from celery import shared_task
from django.conf import settings

from common.analytics import statsd
from common.enums import EventType, FaxStatus
from integration.tasks import sync_ballotrequest_to_actionnetwork
from smsbot.tasks import send_welcome_sms

log = logging.getLogger("absentee")


@shared_task
@statsd.timed("turnout.absentee.ballotrequest_followup")
def ballotrequest_followup(ballotrequest_pk: str) -> None:
    from .models import BallotRequest

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)

    if settings.SMS_POST_SIGNUP_ALERT:
        send_welcome_sms.apply_async(
            args=(str(ballot_request.phone), "absentee"),
            countdown=settings.SMS_OPTIN_REMINDER_DELAY,
        )

    if settings.ACTIONNETWORK_SYNC:
        sync_ballotrequest_to_actionnetwork.delay(ballot_request.uuid)


@shared_task
@statsd.timed("turnout.register.send_ballotrequest_notification")
def send_ballotrequest_notification(ballotrequest_pk: str) -> None:
    from .models import BallotRequest
    from .notification import trigger_notification

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)
    ballot_request.action.track_event(EventType.FINISH_SELF_PRINT)

    trigger_notification(ballot_request)


@shared_task
@statsd.timed("turnout.register.send_ballotrequest_leo_email")
def send_ballotrequest_leo_email(ballotrequest_pk: str) -> None:
    from .models import BallotRequest
    from .leo_email import trigger_leo_email

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)
    ballot_request.action.track_event(EventType.FINISH_LEO)

    trigger_leo_email(ballot_request)


@shared_task
@statsd.timed("turnout.absentee.send_ballotrequest_leo_fax")
def send_ballotrequest_leo_fax(ballotrequest_pk: str) -> None:
    from .models import BallotRequest
    from .leo_fax import send_fax_and_fax_submitted_email

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)
    ballot_request.action.track_event(EventType.FINISH_LEO_FAX_PENDING)

    send_fax_and_fax_submitted_email(ballot_request)


class FaxSubmissionFailedException(Exception):
    pass


@shared_task
@statsd.timed("turnout.absentee.send_ballotrequest_leo_fax_sent_notification")
def send_ballotrequest_leo_fax_sent_notification(
    fax_status_str: str, ballotrequest_pk: str
) -> None:
    from .models import BallotRequest
    from .leo_fax import send_fax_sent_email

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)

    if fax_status_str == str(FaxStatus.PERMANENT_FAILURE):
        ballot_request.action.track_event(EventType.FINISH_LEO_FAX_FAILED)
        sentry_sdk.capture_exception(
            FaxSubmissionFailedException(
                f"Fax submission failed for ballot request {ballotrequest_pk}"
            )
        )
        log.error(f"Fax submission failed for ballot request {ballotrequest_pk}")
    else:
        ballot_request.action.track_event(EventType.FINISH_LEO_FAX_SENT)
        send_fax_sent_email(ballot_request)


@shared_task
def refresh_region_links():
    from .region_links import refresh_region_links

    refresh_region_links()
