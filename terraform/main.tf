terraform {
    required_providers {
        aws = {
            source  = "hashicorp/aws"
            version = "~> 4.0"
        }
    }
}

provider "aws" {
    region = "eu-west-2"
}

variable "mp3_downloader_docker_uri" {
    type = string
}

resource "aws_vpc" "ytmp3-vpc" {
    cidr_block = "10.0.0.0/16"
}

resource "aws_iam_role" "ytmp3-downloader-role" {
    name = "ytmp3-downloader-role"
    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Action = "sts:AssumeRole"
            Principal =  {
                Service = "lambda.amazonaws.com"
            }
            Effect = "Allow"
        }]
    })

    managed_policy_arns = [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    ]
}

resource "aws_lambda_function" "ytmp3-downloader" {
    function_name = "ytmp3-downloader"
    role = aws_iam_role.ytmp3-downloader-role.arn
    description = "ytmp3 downloader service"
    image_uri = var.mp3_downloader_docker_uri
    memory_size = 512
    timeout = 300
    package_type = "Image"
}
