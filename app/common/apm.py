import ddtrace.filters
from ddtrace.tracer import Tracer

tracer = Tracer()
tracer.configure(
    settings={"FILTERS": [ddtrace.filters.FilterRequestsOnUrl(r".+/-/health/$"),],}
)
