import logging

import sentry_sdk
from celery import shared_task
from django.conf import settings

from common.analytics import statsd
from common.enums import EventType, FaxStatus
from mailer.retry import EMAIL_RETRY_PROPS

log = logging.getLogger("absentee")


@shared_task(**EMAIL_RETRY_PROPS)
@statsd.timed("turnout.absentee.send_ballotrequest_notification")
def send_ballotrequest_notification(ballotrequest_pk: str) -> None:
    from .models import BallotRequest
    from .notification import trigger_notification

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)
    if ballot_request.request_mailing_address1:
        ballot_request.action.track_event(EventType.FINISH_LOB)

        # nag them in a few minutes
        send_print_and_forward_confirm_nag.apply_async(
            (ballot_request.uuid,), countdown=settings.ABSENTEE_LOB_CONFIRM_NAG_SECONDS
        )
    else:
        ballot_request.action.track_event(EventType.FINISH_SELF_PRINT)

    trigger_notification(ballot_request)


@shared_task(**EMAIL_RETRY_PROPS)
@statsd.timed("turnout.absentee.send_ballotrequest_leo_email")
def send_ballotrequest_leo_email(ballotrequest_pk: str) -> None:
    from .models import BallotRequest
    from .leo_email import trigger_leo_email

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)
    ballot_request.action.track_event(EventType.FINISH_LEO)

    trigger_leo_email(ballot_request)


# For faxing, the retry is covering both sending the fax to SQS and sending the
# email to the voter. We don't want to duplicate faxes, so all retries must
# complete within SQS's 5-minute retry window.
SQS_RETRY_WINDOW = (5 * 60) - 30  # 30 second slop
FAX_RETRY_PROPS = {
    **EMAIL_RETRY_PROPS,
    "retry_backoff_max": SQS_RETRY_WINDOW / settings.EMAIL_TASK_RETRIES,
}


@shared_task(**FAX_RETRY_PROPS)
@statsd.timed("turnout.absentee.send_ballotrequest_leo_fax")
def send_ballotrequest_leo_fax(ballotrequest_pk: str) -> None:
    from .models import BallotRequest
    from .leo_fax import send_fax_and_fax_submitted_email

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)
    ballot_request.action.track_event(EventType.FINISH_LEO_FAX_PENDING)

    send_fax_and_fax_submitted_email(ballot_request)


class FaxSubmissionFailedException(Exception):
    pass


@shared_task(**EMAIL_RETRY_PROPS)
@statsd.timed("turnout.absentee.send_ballotrequest_leo_fax_sent_notification")
def send_ballotrequest_leo_fax_sent_notification(
    fax_status_str: str, ballotrequest_pk: str
) -> None:
    from .models import BallotRequest
    from .leo_fax import send_fax_sent_email, send_fax_failed_email

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)

    if fax_status_str == str(FaxStatus.PERMANENT_FAILURE):
        ballot_request.action.track_event(EventType.FINISH_LEO_FAX_FAILED)
        sentry_sdk.capture_exception(
            FaxSubmissionFailedException(
                f"Fax submission failed for ballot request {ballotrequest_pk}"
            )
        )
        log.error(f"Fax submission failed for ballot request {ballotrequest_pk}")
        send_fax_failed_email(ballot_request)
    else:
        ballot_request.action.track_event(EventType.FINISH_LEO_FAX_SENT)
        send_fax_sent_email(ballot_request)


@shared_task
def refresh_region_links():
    from .region_links import refresh_region_links

    refresh_region_links()


@shared_task(**EMAIL_RETRY_PROPS)
@statsd.timed("turnout.absentee.send_download_reminder")
def send_download_reminder(pk: str) -> None:
    from .models import BallotRequest
    from .notification import trigger_reminder

    ballot_request = BallotRequest.objects.select_related().get(pk=pk)
    if ballot_request.request_mailing_address1:
        event_type = EventType.FINISH_LOB_CONFIRM
    else:
        event_type = EventType.DOWNLOAD
    if ballot_request.action.event_set.filter(event_type=event_type).exists():
        return
    trigger_reminder(ballot_request)


@shared_task(**EMAIL_RETRY_PROPS)
@statsd.timed("turnout.absentee.send_print_and_forward_nag")
def send_print_and_forward_confirm_nag(pk: str) -> None:
    from .models import BallotRequest
    from .notification import trigger_print_and_forward_confirm_nag

    ballot_request = BallotRequest.objects.select_related().get(pk=pk)
    if ballot_request.action.event_set.filter(
        event_type=EventType.FINISH_LOB_CONFIRM
    ).exists():
        return
    trigger_print_and_forward_confirm_nag(ballot_request)


@shared_task(**EMAIL_RETRY_PROPS)
@statsd.timed("turnout.absentee.external_tool_upsell")
def external_tool_upsell(ballot_request_pk: str) -> None:
    from .models import BallotRequest
    from .notification import trigger_external_tool_upsell
    from smsbot.tasks import send_welcome_sms

    ballot_request = BallotRequest.objects.select_related().get(pk=ballot_request_pk)
    send_welcome_sms(str(ballot_request.phone), "absentee")
    trigger_external_tool_upsell(ballot_request)


@shared_task(**EMAIL_RETRY_PROPS)
@statsd.timed("turnout.absentee.print_and_forward_mailed")
def send_print_and_forward_mailed(
    ballot_request_pk: str, action_pk: str = None
) -> None:
    from .models import BallotRequest
    from .notification import trigger_print_and_forward_mailed
    from smsbot.tasks import send_welcome_sms

    ballot_request = BallotRequest.objects.select_related().get(pk=ballot_request_pk)
    send_welcome_sms(str(ballot_request.phone), "absentee")
    trigger_print_and_forward_mailed(ballot_request)


@shared_task(**EMAIL_RETRY_PROPS)
@statsd.timed("turnout.absentee.print_and_forward_returned")
def send_print_and_forward_returned(
    ballot_request_pk: str, action_pk: str = None
) -> None:
    from .models import BallotRequest
    from .notification import trigger_print_and_forward_returned
    from smsbot.tasks import send_welcome_sms

    ballot_request = BallotRequest.objects.select_related().get(pk=ballot_request_pk)
    send_welcome_sms(str(ballot_request.phone), "absentee")
    trigger_print_and_forward_returned(ballot_request)


@shared_task(**EMAIL_RETRY_PROPS)
@statsd.timed("turnout.absentee.mail_chase")
def send_mail_chase(ballot_request_pk: str, action_pk: str = None) -> None:
    from .models import BallotRequest
    from .notification import trigger_mail_chase
    from smsbot.tasks import send_welcome_sms

    ballot_request = BallotRequest.objects.select_related().get(pk=ballot_request_pk)
    send_welcome_sms(str(ballot_request.phone), "absentee")
    trigger_mail_chase(ballot_request)
