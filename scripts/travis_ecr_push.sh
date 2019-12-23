#!/bin/bash

pip install awscli

eval $(aws ecr get-login --no-include-email --region us-west-2)
docker build -t turnout .
docker tag turnout:latest ${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/turnout:${TRAVIS_TAG}
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/turnout:${TRAVIS_TAG}
