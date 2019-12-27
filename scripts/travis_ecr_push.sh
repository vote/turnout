#!/bin/bash

pip install awscli

eval $(aws ecr get-login --no-include-email --region us-west-2)
docker build --build-arg TAG_ARG=${TRAVIS_TAG} --build-arg BUILD_ARG=${TRAVIS_BUILD} -t turnout .
docker tag turnout:latest ${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/turnout:${TRAVIS_TAG}
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/turnout:${TRAVIS_TAG}
