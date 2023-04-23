#!/bin/bash
set -e

STACK_NAME="ytmp3-cloud"
YTMP3_DOWNLOADER_ECR_REPO_NAME="ytmp3-downloader"

aws cloudformation delete-stack --stack-name $STACK_NAME
aws ecr delete-repository --force --repository-name $YTMP3_DOWNLOADER_ECR_REPO_NAME
