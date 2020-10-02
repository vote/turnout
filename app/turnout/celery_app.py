import os
import time

import celery
import ddtrace
import psycopg2
import redis

from common.apm import tracer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "turnout.settings")

if os.environ.get("DATADOG_API_KEY"):
    ddtrace.patch_all()

app = celery.Celery("turnout")

if os.environ.get("DATADOG_API_KEY"):
    ddtrace.Pin.override(psycopg2, tracer=tracer)
    ddtrace.Pin.override(redis, tracer=tracer)
    ddtrace.Pin.override(app, tracer=tracer)

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    time.sleep(3)
    return {"turnout": "all the voters"}
