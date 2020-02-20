#!/bin/bash

pip install awscli

eval $(aws ecr get-login --no-include-email --region us-west-2)
docker build --build-arg TAG_ARG=dev --build-arg BUILD_ARG=${TRAVIS_BUILD_NUMBER} -t turnoutdev .
docker tag turnoutdev:latest ${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/turnoutdev:${TRAVIS_COMMIT}
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/turnoutdev:${TRAVIS_COMMIT}
