#!/bin/bash

gunicorn -b 0.0.0.0:8000 -c /app/turnout/gunicorn.conf.py turnout.wsgi_prod
