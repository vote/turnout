import datetime
import logging

import sentry_sdk
from django.contrib.postgres.fields import JSONField
from django.db import models

from common.utils.models import TimestampModel, UUIDModel
from turnout.celery_app import app

logger = logging.getLogger("common")


class DelayedTask(UUIDModel, TimestampModel):
    task_name = models.TextField(null=True)
    args = JSONField(null=True)
    kwargs = JSONField(null=True)
    due_at = models.DateTimeField(null=True)

    started_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["due_at", "started_at"]),
        ]

    @staticmethod
    def schedule(
        due_at: datetime.datetime, task_name: str, *args, **kwargs
    ) -> "DelayedTask":
        return DelayedTask.objects.create(
            task_name=task_name, due_at=due_at, args=[*args], kwargs=kwargs,
        )

    @staticmethod
    def schedule_polite(state_id: str, task_name, *args, **kwargs) -> "DelayedTask":
        ## TODO: adjust by state ##
        # next polite time interval
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        if now.hour >= 17:
            # after 6am HT, noon ET; before 8pm ET
            when = now
        elif now.hour < 17:
            # later today
            when = datetime.datetime(
                now.year,
                now.month,
                now.day,
                17,
                0,
                0,  # 1700 UTC == 12pm ET == 9am PT == 6am HT
                tzinfo=datetime.timezone.utc,
            )
        else:
            # tomorrow morning
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            when = datetime.datetime(
                tomorrow.year,
                tomorrow.month,
                tomorrow.day,
                17,
                0,
                0,  # 1700 UTC == 12pm ET == 9am PT == 6am HT
                tzinfo=datetime.timezone.utc,
            )
        return DelayedTask.schedule(when, task_name, *args, **kwargs)

    @staticmethod
    def schedule_days_later_polite(
        state_id: str, days: int, task_name, *args, **kwargs
    ) -> "DelayedTask":
        ## TODO: adjust by state ##
        # tomorrow, politely
        tomorrow = datetime.date.today() + datetime.timedelta(days=days)
        when = datetime.datetime(
            tomorrow.year,
            tomorrow.month,
            tomorrow.day,
            17,
            0,
            0,  # 1700 UTC == 12pm ET == 9am PT == 6am HT
            tzinfo=datetime.timezone.utc,
        )
        return DelayedTask.schedule(when, task_name, *args, **kwargs)

    @staticmethod
    def schedule_tomorrow_polite(
        state_id: str, task_name, *args, **kwargs
    ) -> "DelayedTask":
        return DelayedTask.schedule_days_later_polite(
            state_id, 1, task_name, *args, **kwargs
        )

    def deliver(self):
        self.started_at = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
        self.save()

        try:
            new_id = app.send_task(self.task_name, args=self.args, kwargs=self.kwargs)
        except Exception as e:
            logger.exception(
                f"failed to run task {self.task_name} args {self.args} kwargs {self.kwargs}"
            )
            sentry_sdk.capture_exception(e)
