import datetime
import json
import logging

import dateutil.parser
from celery import shared_task
from django.conf import settings
from django.core.cache import cache

from turnout.celery_app import app

from .models import DelayedTask

logger = logging.getLogger("common")
conn = app.connection_for_read()


# Process a single token: if there is work in the queue, run the task.
@shared_task
def process_token(name):
    from celery.app.trace import _fast_trace_task
    from celery.exceptions import Ignore
    from queue import Empty

    queue = conn.SimpleQueue(name, no_ack=True)
    try:
        item = queue.get(block=False)
        _fast_trace_task(
            item.headers["task"],
            item.headers["id"],
            item.headers,
            json.loads(item.body),
            None,
            None,
        )
    except Empty:
        pass
    raise Ignore


@shared_task
def enqueue_tokens(seconds, slack):
    start = datetime.datetime.now()
    end = start + datetime.timedelta(seconds=seconds)

    # don't reschedule any period we already scheduled
    last = cache.get("bulk_tokens_watermark")
    if last:
        last = dateutil.parser.isoparse(last)
        if last > start:
            start = last
    cache.set("bulk_tokens_watermark", end.isoformat())

    span = (end - start).total_seconds()

    for name, interval in settings.BULK_QUEUE_RATE_LIMITS.items():
        # see if queue is empty
        queue = conn.SimpleQueue(name, no_ack=True)
        if not queue.qsize():
            continue

        # queue some tokens
        for i in range(int(span / interval)):
            process_token.apply_async(
                args=(name,),
                queue=settings.BULK_TOKEN_QUEUE,
                eta=start + datetime.timedelta(seconds=i * interval),
                expire=start + datetime.timedelta(seconds=(i * interval + slack)),
            )


@shared_task
def deliver_delayed_tasks():
    # stop working a bit before when we expect our successor to run
    stop = (
        datetime.datetime.now()
        + datetime.timedelta(minutes=settings.DELAYED_TASKS_INTERVAL)
        - datetime.timedelta(seconds=5)
    )

    for t in DelayedTask.objects.filter(
        started_at__isnull=True,
        due_at__lte=datetime.datetime.now().replace(tzinfo=datetime.timezone.utc),
    ):
        if datetime.datetime.now() >= stop:
            break
        t.deliver()


@shared_task
def test_emails(to: str = None):
    from absentee.leo_fax import trigger_test_fax_emails
    from absentee.leo_email import trigger_test_leo_email
    from absentee.notification import trigger_test_notifications
    from integration.notification import trigger_test_notifications as test_integration
    from multi_tenant.notification import (
        trigger_test_notifications as test_multi_tenant,
    )
    from register.notification import trigger_test_notifications as test_register
    from storage.notification import trigger_test_notification as test_storage
    from subscription.notifications import (
        trigger_test_notifications as test_subscription,
    )
    from verifier.notifications import trigger_test_notifications as test_verify

    if to:
        addrs = [to]
    else:
        addrs = settings.TEST_ADDRS

    logger.info("Sending test absentee fax emails")
    trigger_test_fax_emails(addrs)
    logger.info("Sending test absentee LEO emails")
    trigger_test_leo_email(addrs)
    logger.info("Sending test absentee notifications")
    trigger_test_notifications(addrs)
    logger.info("Sending test integration notifications")
    test_integration(addrs)
    logger.info("Sending test multi_tenant notications")
    test_multi_tenant(addrs)
    logger.info("Sending test register notifications")
    test_register(addrs)
    logger.info("Sending test storage notifications")
    test_storage(addrs)
    logger.info("Sending test subscription notifications")
    test_subscription(addrs)
    logger.info("Sending test verify notifications")
    test_verify(addrs)


@shared_task
def test_optimizely(feature: str = "test_optimizely", var: str = "var"):
    return
