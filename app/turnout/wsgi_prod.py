import os

import ddtrace
import django
import psycopg2
import redis
from django.core.wsgi import get_wsgi_application
from gevent import monkey
from whitenoise import WhiteNoise
import logging
from common.apm import tracer

ddtrace.patch_all()
ddtrace.patch(gevent=True)

ddtrace.Pin.override(django, tracer=tracer)
ddtrace.Pin.override(psycopg2, tracer=tracer)
ddtrace.Pin.override(redis, tracer=tracer)

monkey.patch_all()

logging.basicConfig(level=logging.DEBUG)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "turnout.settings")

application = get_wsgi_application()
application = WhiteNoise(application)
application.add_files("/app/static", prefix="static/")  # type: ignore
