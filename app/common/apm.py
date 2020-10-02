import logging

import ddtrace.filters
from ddtrace.tracer import Tracer
from django.conf import settings

logger = logging.getLogger("apm")


class TurnoutTracer(Tracer):
    def write(self, spans):
        logger.debug(spans)
        if settings.DEBUG:
            return
        return super().write(spans)


class FilterResource(object):
    def __init__(self, resource):
        self.resource = resource

    def process_trace(self, trace):
        logger.debug(trace[0].resource)
        if trace[0].resource == self.resource:
            return None
        return trace


tracer = TurnoutTracer()
tracer.configure(
    settings={
        "FILTERS": [
            FilterResource("common.tasks.enqueue_tokens"),
            FilterResource("common.tasks.process_token"),
            ddtrace.filters.FilterRequestsOnUrl(r".+/-/health/$"),
        ],
    }
)
