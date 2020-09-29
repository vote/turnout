import datetime
import logging

import requests
from celery import shared_task
from dateutil.parser import isoparse
from django.conf import settings

from common.analytics import statsd
from mailer.retry import EMAIL_RETRY_PROPS

from .alloy import get_alloy_freshness
from .models import AlloyDataUpdate

logger = logging.getLogger("verifier")


@shared_task(queue="high-pri", **EMAIL_RETRY_PROPS)
@statsd.timed("turnout.absentee.verifier_external_tool_upsell")
def external_tool_upsell(lookup_pk: str) -> None:
    from .models import Lookup
    from .notifications import trigger_upsell
    from smsbot.tasks import send_welcome_sms

    lookup = Lookup.objects.select_related().get(pk=lookup_pk)
    send_welcome_sms(str(lookup.phone), "verifier")
    trigger_upsell(lookup)


@shared_task
def refresh_alloy_dates():
    freshness = get_alloy_freshness()

    for state, date in freshness.items():
        update_at = isoparse(freshness[state]).replace(tzinfo=datetime.timezone.utc)
        last = (
            AlloyDataUpdate.objects.filter(state=state).order_by("-created_at").first()
        )
        if not last or last.state_update_at != update_at:
            update = AlloyDataUpdate.objects.create(
                state=state, state_update_at=update_at,
            )
            if not last:
                # this is the first time we have observed this state.
                # make the (conservative?) assumption that the data
                # appeared in their API a few days after they pulled
                # it from the state.
                guess = update_at + datetime.timedelta(days=3)
                if guess < update.created_at:
                    update.created_at = guess
                    update.save()

            message = f"Alloy registration data update: {state} {update_at}"
            logger.info(message)

            if settings.SLACK_ALLOY_UPDATE_ENABLED:
                try:
                    r = requests.post(
                        settings.SLACK_ALLOY_UPDATE_WEBHOOK, json={"text": message},
                    )
                    r.raise_for_status()
                except Exception as e:
                    logger.warning(f"Failed to post warning to slack webhook: {e}")
