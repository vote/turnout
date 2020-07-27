#!/bin/bash

ddtrace-run celery -A turnout.celery_app beat --scheduler redbeat.RedBeatScheduler --pidfile="/app/celerybeat-checkable.pid"
