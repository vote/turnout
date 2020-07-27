#!/bin/bash

ddtrace-run celery -A turnout.celery_app worker -Q ${1} --without-heartbeat
