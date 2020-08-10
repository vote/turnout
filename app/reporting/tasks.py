import datetime
import logging

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count

from absentee.models import BallotRequest
from common.analytics import statsd
from multi_tenant.models import Client
from register.models import Registration
from verifier.models import Lookup

from .models import Report
from .notification import trigger_notification
from .runner import report_runner

logger = logging.getLogger("reporting")


@shared_task
@statsd.timed("turnout.reporting.process_report")
def process_report(report_pk: str):
    report = Report.objects.select_related("subscriber").get(pk=report_pk)
    report_runner(report)
    send_report_notification.delay(report_pk)


@shared_task
@statsd.timed("turnout.reporting.send_notification")
def send_report_notification(report_pk: str):
    report = Report.objects.select_related("subscriber", "author").get(pk=report_pk)
    trigger_notification(report)


@shared_task
@statsd.timed("turnout.reporting.calc_all_subscriber_stats")
def calc_all_subscriber_stats():
    OFFSET_SECONDS = 2

    expiration = settings.CALC_STATS_INTERVAL * 60
    limit = expiration / OFFSET_SECONDS

    logger.info(f"Recalculating all subscriber stats (limit {limit})")
    n = 0
    for client in Client.objects.order_by("?")[:limit]:
        calc_subscriber_stats.apply_async(
            (client.uuid,), countdown=n, expires=expiration
        )
        n += OFFSET_SECONDS


@shared_task
@statsd.timed("turnout.reporting.calc_subscriber_stats")
def calc_subscriber_stats(uuid):
    extra = {
        "subscriber_uuid": uuid,
    }
    logger.info("Calculated Subscriber Stats %(subscriber_uuid)s", extra, extra=extra)

    r = {
        "last_updated": datetime.datetime.utcnow(),
    }

    # some totals
    r["register"] = (
        Registration.objects.filter(subscriber_id=uuid)
        .select_related("action", "action__details")
        .count()
    )
    r["verify"] = (
        Lookup.objects.filter(subscriber_id=uuid)
        .select_related("action", "action__details")
        .count()
    )
    r["absentee"] = (
        BallotRequest.objects.filter(subscriber_id=uuid)
        .select_related("action", "action__details")
        .count()
    )

    # breakdown by state
    r["by_state"] = {}
    for i in (
        Lookup.objects.filter(subscriber_id=uuid)
        .select_related("action", "action__details")
        .values("state_id")
        .order_by("state_id")
        .annotate(count=Count("state_id"))
    ):
        if i["state_id"] not in r["by_state"]:
            r["by_state"][i["state_id"]] = {}
        r["by_state"][i["state_id"]]["verify"] = i["count"]
    for i in (
        Registration.objects.filter(subscriber_id=uuid)
        .select_related("action", "action__details")
        .values("state_id")
        .annotate(count=Count("state_id"))
        .order_by("state_id")
    ):
        if i["state_id"] not in r["by_state"]:
            r["by_state"][i["state_id"]] = {}
        r["by_state"][i["state_id"]]["register"] = i["count"]
    for i in (
        BallotRequest.objects.filter(subscriber_id=uuid)
        .select_related("action", "action__details")
        .values("state_id")
        .annotate(count=Count("state_id"))
        .order_by("state_id")
    ):
        if i["state_id"] not in r["by_state"]:
            r["by_state"][i["state_id"]] = {}
        r["by_state"][i["state_id"]]["absentee"] = i["count"]

    cache.set(f"client.stats/{uuid}", r, 24 * 60 * 60)
