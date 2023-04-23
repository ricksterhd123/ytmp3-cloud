import json
import logging
import boto3
import botocore
import os
from datetime import datetime
from yt_dlp import YoutubeDL

logger = logging.getLogger('ytmp3-dispatcher')
logger.setLevel(logging.INFO)

YTMP3_DOWNLOADER_QUEUE_URL = os.environ.get('YTMP3_DOWNLOADER_QUEUE_URL')
YTMP3_DB_NAME = os.environ.get('YTMP3_DB_NAME')

if not YTMP3_DOWNLOADER_QUEUE_URL:
    raise Exception("YTMP3_DOWNLOADER_QUEUE_URL undefined")

if not YTMP3_DB_NAME:
    raise Exception("YTMP3_DB_NAME undefined")


def is_video_id_valid(video_id):
    ydl_opts = {
        "format": "bestaudio/best"
    }

    url = f"https://youtube.com/watch?v={video_id}"

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.sanitize_info(
                ydl.extract_info(url, download=False)
            )

            if not info_dict.get("duration", None):
                return False

    except Exception as e:
        return False

    return True


def put_download_job_to_queue(video_id):
    dyn_table = boto3.resource('dynamodb').Table(YTMP3_DB_NAME)

    try:
        job = {
            'videoId': video_id,
            'status': 'PENDING',
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat()
        }

        dyn_table.put_item(
            Item=job,
            ConditionExpression="attribute_not_exists(#r) or #status = :completeStatus or (#status = :failedStatus)",
            ExpressionAttributeValues={
                ':failedStatus': 'FAILED',
                ':completeStatus': 'COMPLETE'
            },
            ExpressionAttributeNames={
                "#status": "status",
                "#r": "videoId"
            }
        )

        sqs_client = boto3.client('sqs')
        sqs_client.send_message(
            QueueUrl=YTMP3_DOWNLOADER_QUEUE_URL,
            MessageBody=json.dumps({'videoId': video_id}),
        )

        return job
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
            raise
        else:
            # When someone gets this item, update 'updatedAt'
            # dyn_table.update_item(
            #     Key={
            #         'videoId': video_id,
            #     },
            #     AttributeUpdates={
            #         'updatedAt': { 'Value': datetime.now().isoformat(), 'Action': 'PUT' }
            #     }
            # )
            item_result = dyn_table.get_item(
                Key={
                    'videoId': video_id
                }
            )
            return item_result['Item']


def handler(event, context):
    logger.info(event)
    logger.info(context)
    video_id = event['pathParameters']['videoId']

    if not is_video_id_valid(video_id):
        return {
            'statusCode': 400,
            'headers': {
                'content-type': 'application/json',
            },
            'body': json.dumps({
                'error': 'Invalid videoId'
            })
        }

    return {
        'statusCode': 200,
        'headers': {
            'content-type': 'application/json',
        },
        'body': json.dumps(put_download_job_to_queue(video_id))
    }


if __name__ == '__main__':
    print(handler({
        'pathParameters': {
            'videoId': 'ef8Ej3tj9bs'
        }
    }, {}))
