#!/bin/bash
set -e

STACK_NAME="ytmp3-cloud"
aws cloudformation delete-stack --stack-name $STACK_NAME
