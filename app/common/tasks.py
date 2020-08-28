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
