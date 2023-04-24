#!/bin/bash
set -e

## This script assumes the following
## - aws cli installed
## - User has the correct permissions
## - sam cli installed
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

YTMP3_DOWNLOADER_DIR="ytmp3-downloader"
YTMP3_DOWNLOADER_ECR_REPO_NAME=$YTMP3_DOWNLOADER_DIR
YTMP3_STORE_BUCKET_NAME="ytmp3-cloud-mt9olqdw54u4h"

## FIXME: Can't find a better way to check if repository already exists
if ! aws ecr create-repository --repository-name $YTMP3_DOWNLOADER_ECR_REPO_NAME; then
    echo "ECR repository already exists... I think"
fi

cd $SCRIPT_DIR/..

## Fetch a static ffmpeg build and put binaries into ytmp3-downloader/bin for dockerfile
if [[ ! -d "build/" ]]; then
    mkdir -p build
    cd build
    mkdir -p ffmpeg
    cd ffmpeg
    wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz
    wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz.md5
    md5sum -c ffmpeg-git-amd64-static.tar.xz.md5
    tar xvf ffmpeg-git-amd64-static.tar.xz
    mkdir -p ../../$YTMP3_DOWNLOADER_ECR_REPO_NAME/bin
    mv ffmpeg-git-*-amd64-static/ffmpeg ffmpeg-git-*-amd64-static/ffprobe ../../$YTMP3_DOWNLOADER_ECR_REPO_NAME/bin
    cd ..
    cd ..
fi

## Build docker image and push into ecr repository
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com
docker build -t $YTMP3_DOWNLOADER_ECR_REPO_NAME $YTMP3_DOWNLOADER_ECR_REPO_NAME/
docker tag $YTMP3_DOWNLOADER_ECR_REPO_NAME:latest $ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/$YTMP3_DOWNLOADER_ECR_REPO_NAME:latest
docker push $ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/$YTMP3_DOWNLOADER_ECR_REPO_NAME:latest
YTMP3_DOWNLOADER_DOCKER_IMAGE_URI=$(docker inspect --format='{{index .RepoDigests 0}}' $YTMP3_DOWNLOADER_ECR_REPO_NAME:latest)

## Build the template and deploy guided
sam build --use-container
sam deploy --confirm-changeset --no-fail-on-empty-changeset --image-repository=$YTMP3_DOWNLOADER_DOCKER_IMAGE_URI --parameter-overrides Ytmp3DownloaderDockerImageUri=$YTMP3_DOWNLOADER_DOCKER_IMAGE_URI Ytmp3StoreBucketName=$YTMP3_STORE_BUCKET_NAME
