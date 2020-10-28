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


class FilterTrivialResource(object):
    def __init__(self, resource):
        self.resource = resource

    def process_trace(self, trace):
        logger.debug(trace[0].resource)
        if trace[0].resource == self.resource and len(trace) == 1:
            return None
        return trace


tracer = TurnoutTracer()
tracer.configure(
    settings={
        "FILTERS": [
            FilterTrivialResource("common.tasks.enqueue_tokens"),
            FilterTrivialResource("common.tasks.process_token"),
            ddtrace.filters.FilterRequestsOnUrl(r".+/-/health/$"),
        ],
    }
)
