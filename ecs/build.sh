#!/bin/bash

set -eu

cd "$(dirname "$0")"

# the container assumes the uid is 1000; mangle permissions to behave
# if we're not.
TARGETS="../scripts/remote_run.sh */*/*.json ./v2/template/include/*.libsonnet ./v2/template/*.jsonnet"
TARGETDIRS="v2/generated/*"
chmod 777 $TARGETS $TARGETDIRS

cat <<"EOF" | docker run --rm -i --entrypoint bash -v $PWD/..:/app -w /app/ecs bitnami/jsonnet:latest
jsonnetfmt -i ./v2/template/*.jsonnet
jsonnetfmt -i ./v2/template/include/*.libsonnet


jsonnet ./v2/template/service_web.jsonnet --ext-str env=dev > ./v2/generated/dev/service_web.task.json
jsonnet ./v2/template/service_beat.jsonnet --ext-str env=dev > ./v2/generated/dev/service_beat.task.json
jsonnet ./v2/template/service_worker.jsonnet --ext-str env=dev > ./v2/generated/dev/service_worker.task.json

jsonnet ./v2/template/service_web.jsonnet --ext-str env=staging > ./v2/generated/staging/service_web.task.json
jsonnet ./v2/template/service_beat.jsonnet --ext-str env=staging > ./v2/generated/staging/service_beat.task.json
jsonnet ./v2/template/service_worker.jsonnet --ext-str env=staging > ./v2/generated/staging/service_worker.task.json

jsonnet ./v2/template/service_web.jsonnet --ext-str env=prod > ./v2/generated/prod/service_web.task.json
jsonnet ./v2/template/service_beat.jsonnet --ext-str env=prod > ./v2/generated/prod/service_beat.task.json
jsonnet ./v2/template/service_worker.jsonnet --ext-str env=prod > ./v2/generated/prod/service_worker.task.json

jsonnet -S ./v2/template/remote_run.jsonnet --ext-str env=prod > ../scripts/remote_run.sh
EOF

chmod 644 $TARGETS
chmod 755 $TARGETDIRS
