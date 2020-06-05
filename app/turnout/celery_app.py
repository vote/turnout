import os
import time

from celery import Celery
from ddtrace import patch, patch_all

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "turnout.settings")

if os.environ.get("DEBUG") != "True":
    patch_all()
    patch(celery=True)

app = Celery("turnout")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    time.sleep(3)
    return {"turnout": "all the voters"}
