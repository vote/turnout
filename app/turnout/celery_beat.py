import threading

import redis
from django.conf import settings

from common.aws import cloudwatch_client

from .celery_app import app

print("Beat Schedule")
print(app.conf.beat_schedule)

queue_names = [q.name for q in settings.CELERY_TASK_QUEUES]


def report_stats():
    threading.Timer(settings.BEAT_STATS_INTERVAL, report_stats).start()

    conn = redis.from_url(settings.CELERY_BROKER_URL)
    queue_len = sum(conn.llen(name) for name in queue_names)

    print(f"Queue Length: {queue_len}", flush=True)

    if settings.BEAT_STATS_METRIC_NAMESPACE:
        cloudwatch_client.put_metric_data(
            Namespace=settings.BEAT_STATS_METRIC_NAMESPACE,
            MetricData=[
                {
                    "MetricName": "celery_queue_length",
                    "Dimensions": [{"Name": "Env", "Value": settings.ENV}],
                    "Value": queue_len,
                    "Unit": "Count",
                },
            ],
        )


threading.Timer(settings.BEAT_STATS_INTERVAL, report_stats).start()
