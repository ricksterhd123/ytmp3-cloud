#!/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $SCRIPT_DIR/..
rm -rf .aws-sam/
rm -rf build/
rm -rf ytmp3-downloader-layer/bin
