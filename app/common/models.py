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
    def schedule(due_at: datetime.datetime, task_name: str, *args, **kwargs) -> None:
        DelayedTask.objects.create(
            task_name=task_name, due_at=due_at, args=[*args], kwargs=kwargs,
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
