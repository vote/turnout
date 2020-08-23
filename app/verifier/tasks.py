from celery import shared_task

from common.analytics import statsd
from mailer.retry import EMAIL_RETRY_PROPS


@shared_task(**EMAIL_RETRY_PROPS)
@statsd.timed("turnout.absentee.verifier_external_tool_upsell")
def external_tool_upsell(lookup_pk: str) -> None:
    from .models import Lookup
    from .notifications import trigger_upsell

    lookup = Lookup.objects.select_related().get(pk=lookup_pk)
    trigger_upsell(lookup)
