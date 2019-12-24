FROM python:3.7-buster
ENV APP_DIR=/app
WORKDIR $APP_DIR
COPY app/ $APP_DIR/
COPY scripts/docker_build.sh /root/
RUN bash /root/docker_build.sh
EXPOSE 8000
CMD ["ddtrace-run", "gunicorn", "-b", "0.0.0.0:8000", "-c", "/app/turnout/gunicorn.conf.py", "turnout.wsgi"]
