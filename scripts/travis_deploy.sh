#!/bin/bash

pip install awscli

eval $(aws ecr get-login --no-include-email --region us-west-2)
docker build --build-arg TAG_ARG=${TRAVIS_TAG} --build-arg BUILD_ARG=${TRAVIS_BUILD_NUMBER} -t turnout .
docker tag turnout:latest ${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/turnout:${TRAVIS_TAG}
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/turnout:${TRAVIS_TAG}


curl https://sentry.io/api/0/organizations/${SENTRY_ORG}/releases/ \
  -X POST \
  -H "Authorization: Bearer ${SENTRY_AUTH_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "
{
    \"version\": \"turnout@${TRAVIS_TAG}\",
    \"refs\": [{
        \"repository\":\"vote/turnout\",
        \"commit\":\"${TRAVIS_COMMIT}\"
    }],
    \"projects\":[\"turnout\"]
}"
