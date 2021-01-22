#!/bin/bash

REGION=${REGION:-us-west-2}
DOCKER_REPO_NAME=${DOCKER_REPO_NAME:-turnoutdev}
ACCOUNT_ID=$(aws sts get-caller-identity | jq -r ".Account")

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_TIME=$(date "+%Y.%m.%d-%H.%M.%S")
CURRENT_USER=$(git config user.email)
TAG_NAME=$(echo $CURRENT_BRANCH$CURRENT_USER$CURRENT_TIME | iconv -t ascii//TRANSLIT | sed -E s/[^a-zA-Z0-9]+/-/g | sed -E s/-+\//g | tr A-Z a-z)

echo "Uploading Tag ${TAG_NAME}"

ACCOUNT_ID=$(aws sts get-caller-identity | jq -r ".Account")
IMAGE=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$DOCKER_REPO_NAME:$TAG_NAME

echo "Logging into ECR"
if aws --version | grep -q aws-cli/1; then
  eval $(aws ecr get-login --no-include-email --region $REGION)
else
  aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
fi

docker build --build-arg TAG_ARG=dev --build-arg BUILD_ARG=${TAG_NAME} -t ${IMAGE} .
docker push ${IMAGE}
