import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task
from django.db import connection, transaction

from common.analytics import statsd
from mailer.retry import EMAIL_RETRY_PROPS

from .models import Report, StatsRefresh
from .notification import trigger_notification
from .runner import report_runner

logger = logging.getLogger("reporting")


@shared_task
@statsd.timed("turnout.reporting.process_report")
def process_report(report_pk: str):
    report = Report.objects.select_related("subscriber").get(pk=report_pk)
    report_runner(report)
    send_report_notification.delay(report_pk)


@shared_task(**EMAIL_RETRY_PROPS)
@statsd.timed("turnout.reporting.send_notification")
def send_report_notification(report_pk: str):
    report = Report.objects.select_related("subscriber", "author").get(pk=report_pk)
    trigger_notification(report)


@shared_task
@statsd.timed("turnout.reporting.calc_all_subscriber_stats")
def calc_all_subscriber_stats():
    with transaction.atomic():
        with connection.cursor() as cursor:
            # We fetch stats starting from the last update time, and going until (now - 1 minute).
            # The 1 minute offset is to account for differences between the DB clock and
            # the app server clock -- if the app server is ahead of the DB, we don't
            # want to think that we have data up to, e.g. 4PM if the DB thinks it's 3:59PM.
            current_update_time = datetime.now(tz=timezone.utc) - timedelta(minutes=1)
            refresh_obj = StatsRefresh.objects.all()[0]

            SQL_QUERY = """
                INSERT INTO reporting_subscriberstats (uuid, partner_id, tool, count)
                (
                    SELECT
                    uuid_generate_v4() AS uuid,
                    partner_id,
                    'register' AS tool,
                    COUNT(*)
                    FROM register_registration
                    WHERE created_at > %(start_time)s AND created_at <= %(end_time)s
                    GROUP BY partner_id

                    UNION ALL

                    SELECT
                    uuid_generate_v4() AS uuid,
                    partner_id,
                    'verify' AS tool,
                    COUNT(*)
                    FROM verifier_lookup
                    WHERE created_at > %(start_time)s AND created_at <= %(end_time)s
                    GROUP BY partner_id

                    UNION ALL

                    SELECT
                    uuid_generate_v4() AS uuid,
                    partner_id,
                    'absentee' AS tool,
                    COUNT(*)
                    FROM absentee_ballotrequest
                    WHERE created_at > %(start_time)s AND created_at <= %(end_time)s
                    GROUP BY partner_id

                    UNION ALL

                    SELECT
                    uuid_generate_v4() AS uuid,
                    partner_id,
                    'locate' AS tool,
                    COUNT(*)
                    FROM polling_place_pollingplacelookup
                    WHERE created_at > %(start_time)s AND created_at <= %(end_time)s
                    GROUP BY partner_id
                )
                ON CONFLICT (partner_id, tool)
                DO UPDATE SET count = reporting_subscriberstats.count + excluded.count
            """

            cursor.execute(
                SQL_QUERY,
                {"start_time": refresh_obj.last_run, "end_time": current_update_time},
            )

            StatsRefresh.objects.update(last_run=current_update_time)
