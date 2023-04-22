#! /bin/bash
set -e

## This script assumes the following
## - aws cli installed
## - User has the correct permissions
## - sam cli installed
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
ECR_REPO_NAME="ytmp3-downloader"
YTMP3_STORE_BUCKET_NAME="bpmqrjcb"

if ! aws ecr create-repository --repository-name $ECR_REPO_NAME; then
    ## FIXME: Can't find a better way to check if repository already exists,
    ## I said this script assumes you have the correct permissions...
    echo "ECR repository already exists... I think"
fi

cd $SCRIPT_DIR/..
mkdir -p build
cd build

## Fetch a static ffmpeg build and put binaries into mp3-downloader/bin for dockerfile
mkdir -p ffmpeg
cd ffmpeg
wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz
wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz.md5
md5sum -c ffmpeg-git-amd64-static.tar.xz.md5
tar xvf ffmpeg-git-amd64-static.tar.xz
mkdir -p ../../mp3-downloader/bin
mv ffmpeg-git-*-amd64-static/ffmpeg ffmpeg-git-*-amd64-static/ffprobe ../../mp3-downloader/bin
cd ..
cd ..

## Build docker image and push into ecr repository
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com
docker build -t $ECR_REPO_NAME mp3-downloader/
docker tag $ECR_REPO_NAME:latest $ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/$ECR_REPO_NAME:latest
docker push $ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/$ECR_REPO_NAME:latest
YTMP3_DOWNLOADER_DOCKER_IMAGE_URI=$(docker inspect --format='{{index .RepoDigests 0}}' $ECR_REPO_NAME:latest)

## Build the template and deploy guided
sam build
sam deploy --guided --parameter-overrides Ytmp3DownloaderDockerImageUri=$YTMP3_DOWNLOADER_DOCKER_IMAGE_URI Ytmp3StoreBucketName=$YTMP3_STORE_BUCKET_NAME
