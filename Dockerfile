FROM python:3.7-buster
RUN apt-get update && apt-get install -y \
    wait-for-it && apt-get clean
ENV APP_DIR=/app \
    PYTHONBUFFERED=1
WORKDIR $APP_DIR
COPY app/requirements.txt $APP_DIR
RUN pip install -r requirements.txt && rm -rf /root/.cache
COPY app/ $APP_DIR/
EXPOSE 8000
CMD ["ddtrace-run", "gunicorn", "-b", "0.0.0.0:8000", "-c", "/app/turnout/gunicorn.conf.py", "turnout.wsgi"]
