import os

import datadog
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "turnout.settings")

STATSD_TAGS = [
    f'env:{os.environ.get("CLOUD_STACK", default="")}',
    f'spinnaker_detail:{os.environ.get("CLOUD_DETAIL", default="")}',
    f'spinnaker_servergroup:{os.environ.get("SERVER_GROUP", default="")}',
    f'spinnaker_stack:{os.environ.get("CLOUD_STACK", default="")}',
    f'image_tag:{os.environ.get("TAG", default="")}',
    f'build:{os.environ.get("BUILD", default="")}',
]
datadog.initialize(statsd_constant_tags=STATSD_TAGS)

application = get_wsgi_application()
application = WhiteNoise(application)
application.add_files("/app/static", prefix="static/")
