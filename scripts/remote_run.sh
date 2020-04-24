#!/bin/bash

REGION=${REGION:-us-west-2}
ENVIRONMENT=${ENVIRONMENT:-staging}
DOCKER_REPO_NAME=${DOCKER_REPO_NAME:-turnout}
DEBUG=${DEBUG:-true}
ACCOUNT_ID=$(aws sts get-caller-identity | jq -r ".Account")

if [ $1 ]; then

echo "Logging into ECR"
eval $(aws ecr get-login --no-include-email --region $REGION)

fi

echo "Account ID: $ACCOUNT_ID"

export ALLOWED_HOSTS=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.allowed_hosts | jq '.Parameter["Value"]' -r)
export DATABASE_URL=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.database_url | jq '.Parameter["Value"]' -r)
export SECRET_KEY=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.secret_key | jq '.Parameter["Value"]' -r)
export REDIS_URL=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.redis_url | jq '.Parameter["Value"]' -r)
export SENTRY_DSN=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.sentry_dsn | jq '.Parameter["Value"]' -r)
export TARGETSMART_KEY=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.targetsmart_key | jq '.Parameter["Value"]' -r)
export MULTIFACTOR_ISSUER=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.multifactor_issuer | jq '.Parameter["Value"]' -r)
export ATTACHMENT_USE_S3=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.use_s3 | jq '.Parameter["Value"]' -r)
export AWS_STORAGE_BUCKET_NAME=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.public_storage_bucket | jq '.Parameter["Value"]' -r)
export AWS_STORAGE_PRIVATE_BUCKET_NAME=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.private_storage_bucket | jq '.Parameter["Value"]' -r)
export SENDGRID_API_KEY=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.sendgrid_api_key | jq '.Parameter["Value"]' -r)
export FILE_TOKEN_RESET_URL=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.file_token_reset_url | jq '.Parameter["Value"]' -r)
export PRIMARY_ORIGIN=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.primary_origin | jq '.Parameter["Value"]' -r)
export USVOTEFOUNDATION_KEY=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.usvf_key | jq '.Parameter["Value"]' -r)
export ALLOY_KEY=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.alloy_key | jq '.Parameter["Value"]' -r)
export ALLOY_SECRET=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.alloy_secret | jq '.Parameter["Value"]' -r)

echo "Parameters Acquired"


AWS_CRED_DETAILS=$(aws sts get-session-token --duration-seconds 86400)
export AWS_ACCESS_KEY_ID=$(echo $AWS_CRED_DETAILS | jq '.Credentials["AccessKeyId"]' -r)
export AWS_SECRET_ACCESS_KEY=$(echo $AWS_CRED_DETAILS | jq '.Credentials["SecretAccessKey"]' -r)
export AWS_DEFAULT_REGION=$REGION

echo "AWS Credentials Acquired"


if [ $1 ]; then

IMAGE=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$DOCKER_REPO_NAME:$1

else

echo "Building From Local"
docker build --cache-from voteamerica/turnout-ci-cache:latest --build-arg TAG_ARG=local --build-arg BUILD_ARG=0 -t turnout_full .
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
           -e MULTIFACTOR_ISSUER \
           -e ATTACHMENT_USE_S3 \
           -e AWS_STORAGE_BUCKET_NAME \
           -e AWS_STORAGE_PRIVATE_BUCKET_NAME \
           -e SENDGRID_API_KEY \
           -e FILE_TOKEN_RESET_URL \
           -e PRIMARY_ORIGIN \
           -e AWS_ACCESS_KEY_ID \
           -e AWS_SECRET_ACCESS_KEY \
           -e AWS_DEFAULT_REGION \
           -e USVOTEFOUNDATION_KEY \
           -e ALLOY_KEY \
           -e ALLOY_SECRET \
           -e DEBUG=$DEBUG \
           -p 8000:8000 \
           $IMAGE \
           /bin/bash
