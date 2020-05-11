from celery import shared_task

from common.analytics import statsd
from common.enums import TurnoutActionStatus


@shared_task
@statsd.timed("turnout.absentee.process_ballotrequest_submission")
def process_ballotrequest_submission(
    ballotrequest_pk: str, state_id_number: str, is_18_or_over: bool
) -> None:
    from .models import BallotRequest
    from .generateform import process_ballot_request

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)
    process_ballot_request(ballot_request, state_id_number, is_18_or_over)


@shared_task
@statsd.timed("turnout.register.send_ballotrequest_notification")
def send_ballotrequest_notification(ballotrequest_pk: str) -> None:
    from .models import BallotRequest
    from .notification import trigger_notification

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)
    ballot_request.status = TurnoutActionStatus.PDF_SENT
    ballot_request.save(update_fields=["status"])

    trigger_notification(ballot_request)


@shared_task
@statsd.timed("turnout.register.send_ballotrequest_leo_email")
def send_ballotrequest_leo_email(ballotrequest_pk: str) -> None:
    from .models import BallotRequest
    from .leo_email import trigger_leo_email

    ballot_request = BallotRequest.objects.select_related().get(pk=ballotrequest_pk)
    ballot_request.status = TurnoutActionStatus.PDF_SENT
    ballot_request.save(update_fields=["status"])

    trigger_leo_email(ballot_request)
