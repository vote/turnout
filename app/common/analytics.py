from datadog import DogStatsd
from django.conf import settings


class TurnoutStatsd(DogStatsd):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.constant_tags = self.constant_tags + settings.STATSD_TAGS


statsd = TurnoutStatsd()
