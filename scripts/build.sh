#!/bin/bash

set -e 

ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
ECR_REPO_NAME="ytmp3-downloader"

aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com
docker build -t $ECR_REPO_NAME mp3-downloader/
docker tag $ECR_REPO_NAME:latest $ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/$ECR_REPO_NAME:latest
docker push $ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/$ECR_REPO_NAME:latest

echo $(docker inspect --format='{{index .RepoDigests 0}}' $ECR_REPO_NAME:latest)
