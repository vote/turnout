#!/bin/bash

celery inspect ping -A turnout.celery_app -d celery@$HOSTNAME
