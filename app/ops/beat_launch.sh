#!/bin/bash

ddtrace-run celery -A turnout.celery_beat beat --scheduler redbeat.RedBeatScheduler --pidfile="/app/celerybeat-checkable.pid"
