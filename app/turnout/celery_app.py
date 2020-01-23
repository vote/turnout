import os
import time

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "turnout.settings")

app = Celery("turnout")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    time.sleep(3)
    return {"turnout": "all the voters"}
