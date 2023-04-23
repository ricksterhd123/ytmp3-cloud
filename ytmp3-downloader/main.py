import logging
import os
import boto3
import json

from yt_dlp import YoutubeDL
from botocore.exceptions import ClientError
from datetime import datetime

logger = logging.getLogger('mp3-downloader')
logger.setLevel(logging.INFO)

AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION')
YTMP3_STORE_BUCKET_NAME = os.environ.get('YTMP3_STORE_BUCKET_NAME')
YTMP3_DOWNLOADER_QUEUE_URL = os.environ.get('YTMP3_DOWNLOADER_QUEUE_URL')
YTMP3_DB_NAME = os.environ.get('YTMP3_DB_NAME')

if not AWS_DEFAULT_REGION:
    raise Exception('AWS_DEFAULT_REGION undefined')

if not YTMP3_STORE_BUCKET_NAME:
    raise Exception("YTMP3_STORE_BUCKET_NAME undefined")

if not YTMP3_DOWNLOADER_QUEUE_URL:
    raise Exception("YTMP3_DOWNLOADER_QUEUE_URL undefined")

if not YTMP3_DB_NAME:
    raise Exception("YTMP3_DB_NAME undefined")


def upload_file(file_name, bucket, object_name=None):
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    s3_client.upload_file(file_name, bucket, object_name)


def handler(sqs_event, context):
    logger.info(sqs_event)
    logger.info(context)

    dyn_table = boto3.resource('dynamodb').Table(YTMP3_DB_NAME)
    sqs_client = boto3.client('sqs')
    jobs = sqs_event['Records']

    for job in jobs:
        try:
            job_id = job['messageId']
            job_reciept_handle = job['receiptHandle']
            job_body = json.loads(job['body'])
            videoId = job_body['videoId']

            if not videoId:
                return {
                    "statusCode": 400
                }

            file_path = '/tmp'
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{file_path}/%(display_id)s.%(ext)s",
                'postprocessors': [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    },
                    {'key': 'FFmpegMetadata'},
                    {'key': 'EmbedThumbnail'}
                ],
                "logger": logger,
            }

            url = f"https://youtube.com/watch?v={videoId}"

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.sanitize_info(
                    ydl.extract_info(url, download=False)
                )

                video_id = info_dict.get("display_id", None)
                duration = info_dict.get("duration", None)
                file_name = f"{video_id}.mp3"

                logger.info(f"Video ID: {video_id}, Duration: {duration}")

                ydl.download([url])
                upload_file(f"{file_path}/{file_name}",
                            YTMP3_STORE_BUCKET_NAME, file_name)
                logger.info(f"Finished downloading video {video_id}")

                dyn_table.update_item(
                    Key={
                        'videoId': video_id,
                    },
                    AttributeUpdates={
                        'updatedAt': {
                            'Value': datetime.now().isoformat(),
                            'Action': 'PUT'
                        },
                        'status': {
                            'Value': 'COMPLETE',
                            'Action': 'PUT'
                        },
                        'url': {
                            'Value': f"{YTMP3_STORE_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{file_name}",
                            'Action': 'PUT'
                        }
                    }
                )

        except Exception as e:
            logger.error(f'Failed to process job {job_id}')
            logger.error(e)
            sqs_client.delete_message(
                QueueUrl=YTMP3_DOWNLOADER_QUEUE_URL,
                ReceiptHandle=job_reciept_handle
            )
            dyn_table.update_item(
                Key={
                    'videoId': video_id,
                },
                AttributeUpdates={
                    'updatedAt': {
                        'Value': datetime.now().isoformat(),
                        'Action': 'PUT'
                    },
                    'status': {
                        'Value': 'FAILED',
                        'Action': 'PUT'
                    },
                    'error': {
                        'Value': f'Failed to download {video_id}, please try again in 1 minute',
                        'Action': 'PUT'
                    }
                }
            )
            return {
                "statusCode": 500
            }

    return {
        "statusCode": 200
    }
