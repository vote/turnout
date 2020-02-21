#!/bin/bash

REGION=${REGION:-us-west-2}
ENVIRONMENT=${ENVIRONMENT:-staging}
DOCKER_REPO_NAME=${DOCKER_REPO_NAME:-turnout}
DEBUG=${DEBUG:-true}
ACCOUNT_ID=$(aws sts get-caller-identity | jq -r ".Account")

echo "Account ID: $ACCOUNT_ID"

export ALLOWED_HOSTS=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.allowed_hosts | jq '.Parameter["Value"]' -r)
export DATABASE_URL=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.database_url | jq '.Parameter["Value"]' -r)
export SECRET_KEY=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.secret_key | jq '.Parameter["Value"]' -r)
export REDIS_URL=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.redis_url | jq '.Parameter["Value"]' -r)
export SENTRY_DSN=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.sentry_dsn | jq '.Parameter["Value"]' -r)
export TARGETSMART_KEY=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.targetsmart_key | jq '.Parameter["Value"]' -r)

echo "Parameters Acquired"

if [ $1 ]; then

echo "Logging into ECR"
eval $(aws ecr get-login --no-include-email --region $REGION)
IMAGE=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$DOCKER_REPO_NAME:$1

else

echo "Building From Local"
docker build --build-arg TAG_ARG=local --build-arg BUILD_ARG=0 -t turnout_full .
IMAGE=turnout_full:latest

fi

echo "Running Image $IMAGE"
docker run -i -t \
           -e ALLOWED_HOSTS \
           -e DATABASE_URL \
           -e SECRET_KEY \
           -e REDIS_URL \
           -e SENTRY_DSN \
           -e TARGETSMART_KEY \
           -e DEBUG=$DEBUG \
           -p 8000:8000 \
           $IMAGE \
           /bin/bash
