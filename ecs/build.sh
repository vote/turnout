#!/bin/bash

set -eu

cd "$(dirname "$0")"

# the container assumes the uid is 1000; mangle permissions to behave
# if we're not.
TARGETS="../scripts/remote_run.sh */*/*.json ./template/include/*.libsonnet ./template/*.jsonnet"
chmod 777 $TARGETS

cat <<"EOF" | docker run --rm -i --entrypoint bash -v $PWD/..:/app -w /app/ecs bitnami/jsonnet:latest
jsonnetfmt -i ./template/*.jsonnet
jsonnetfmt -i ./template/include/*.libsonnet

jsonnet ./template/ecs.jsonnet --ext-str env=dev --ext-code migrations=true > ./generated/dev/turnout_dev_web.task.json
jsonnet ./template/ecs.jsonnet --ext-str env=staging --ext-code migrations=true > ./generated/staging/turnout_staging_web.task.json
jsonnet ./template/ecs.jsonnet --ext-str env=prod --ext-code migrations=false > ./generated/prod/turnout_prod_web.task.json

jsonnet -S ./template/remote_run.jsonnet --ext-str env=prod --ext-code migrations=false > ../scripts/remote_run.sh
EOF

chmod 644 $TARGETS
