FROM python:3.7-buster
ENV APP_DIR=/app
WORKDIR $APP_DIR
COPY scripts/docker_build_step1.sh scripts/docker_build_step2.sh /root/
COPY app/requirements.txt app/package.json app/package-lock.json $APP_DIR/
RUN bash /root/docker_build_step1.sh
COPY app/ $APP_DIR/
RUN bash /root/docker_build_step2.sh

ARG TAG_ARG
ARG BUILD_ARG
ENV TAG=$TAG_ARG
ENV BUILD=$BUILD_ARG

EXPOSE 8000
CMD ["ddtrace-run", "gunicorn", "-b", "0.0.0.0:8000", "-c", "/app/turnout/gunicorn.conf.py", "turnout.wsgi"]
