import datetime
import logging

from celery import shared_task
from django.conf import settings

from .models import DelayedTask

logger = logging.getLogger("common")


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
