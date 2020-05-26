from celery import shared_task

from common.analytics import statsd

from .models import Report
from .notification import trigger_notification
from .runner import report_runner


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
