#!/bin/bash

REGION=${REGION:-us-west-2}
INSTANCENAME=${INSTANCENAME:-turnout-staging}
USERNAME=${USERNAME:-turnout_rds_iam}
DATABASE=${DATABASE:-turnout}

export PGUSER=$USERNAME
export PGHOST=$(aws rds describe-db-instances --filters "Name=db-instance-id,Values=$INSTANCENAME" --region $REGION | jq -r '.["DBInstances"][0]["Endpoint"]["Address"]')
export PGPASSWORD="$(aws rds generate-db-auth-token --hostname $PGHOST --port 5432 --region $REGION --username $USERNAME)"

echo "Dumping $DATABASE"
pg_dump -Fc --no-acl --no-owner -d $DATABASE > dump.backup

export PGUSER=postgres
export PGHOST=localhost
export PGPASSWORD=turnout
export PGPORT=5432

echo "Dropping Schema"
psql -d turnout -c 'DROP SCHEMA public CASCADE;CREATE SCHEMA public;'

echo "Restoring"
pg_restore --verbose --no-owner -d turnout dump.backup

rm dump.backup
