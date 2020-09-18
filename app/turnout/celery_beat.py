import threading

import redis
from django.conf import settings

from common.aws import cloudwatch_client

from .celery_app import app

print("Beat Schedule")
print(app.conf.beat_schedule)
