from celery import shared_task

from common.analytics import statsd


@shared_task
@statsd.timed("turnout.absentee.process_ballotrequest_submission")
def process_ballotrequest_submission(
    ballotrequest_pk: str, state_id_number: str, is_18_or_over: bool
) -> None:
    pass
