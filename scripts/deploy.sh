#!/bin/bash
set -e

## FIXME: Automate these checks
## This script assumes the following
## - aws cli installed
## - User has the correct permissions
## - sam cli installed

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

YTMP3_DOWNLOADER_LAYER_DIR="ytmp3-downloader-layer"
YTMP3_STORE_BUCKET_NAME="ytmp3-cloud-53cqewmhu4xre"

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
    mkdir -p ../../$YTMP3_DOWNLOADER_LAYER_DIR/bin
    mv ffmpeg-git-*-amd64-static/ffmpeg ffmpeg-git-*-amd64-static/ffprobe ../../$YTMP3_DOWNLOADER_LAYER_DIR/bin
    cd ..
    cd ..
fi

## Build the template and deploy guided
sam build --use-container
sam deploy --confirm-changeset --no-fail-on-empty-changeset --parameter-overrides Ytmp3StoreBucketName=$YTMP3_STORE_BUCKET_NAME
