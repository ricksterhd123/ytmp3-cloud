import json
import logging
import boto3
import botocore
import os
import re
from datetime import datetime
from yt_dlp import YoutubeDL

logger = logging.getLogger('ytmp3-dispatcher')
logger.setLevel(logging.INFO)

MAX_VIDEO_DURATION_MINS = 90
YTMP3_DOWNLOADER_QUEUE_URL = os.environ.get('YTMP3_DOWNLOADER_QUEUE_URL')
YTMP3_DB_NAME = os.environ.get('YTMP3_DB_NAME')
YTMP3_STORE_BUCKET_NAME = os.environ.get('YTMP3_STORE_BUCKET_NAME')

if not YTMP3_DOWNLOADER_QUEUE_URL:
    raise Exception('YTMP3_DOWNLOADER_QUEUE_URL undefined')

if not YTMP3_DB_NAME:
    raise Exception('YTMP3_DB_NAME undefined')

if not YTMP3_STORE_BUCKET_NAME:
    raise Exception('YTMP3_STORE_BUCKET_NAME undefined')

sqs_client = boto3.client('sqs')
dyn_table = boto3.resource('dynamodb').Table(YTMP3_DB_NAME)
s3_client = boto3.client('s3')

video_id_regex = re.compile(r"[a-zA-Z0-9_]+")

def is_video_id_valid(video_id):
    # This prevents injecting extra query parameters in the url
    # and remove nasties like &list=
    if not video_id_regex.match(video_id):
        return False, 'Invalid videoId'

    ydl_opts = {
        'format': 'bestaudio/best',
        'allowed_extractors': ['youtube']
    }

    url = f'https://youtube.com/watch?v={video_id}'

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.sanitize_info(
                ydl.extract_info(url, download=False)
            )

            duration = info_dict.get('duration', None)
            if not duration:
                return False, 'No duration in metadata'

            if duration > MAX_VIDEO_DURATION_MINS * 60:
                return False, f'Video exceeds {MAX_VIDEO_DURATION_MINS} minutes'
    except Exception as e:
        return False, 'Video unavailable'

    return True, None


def is_in_store(video_id):
    try:
        s3_client.head_object(
            Bucket=YTMP3_STORE_BUCKET_NAME,
            Key=f'{video_id}.mp3'
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != '404':
            raise
        else:
            return False
    return True

def get_download_job_from_db(video_id):
    item_result = dyn_table.get_item(
        Key={
            'videoId': video_id
        }
    )

    item = item_result.get('Item')
    if not item:
        return False

    return item


def put_download_job_to_queue(video_id, forced=False):
    try:
        job = {
            'videoId': video_id,
            'status': 'PENDING',
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat()
        }

        if not forced:
            dyn_table.put_item(
                Item=job,
                ConditionExpression='attribute_not_exists(#r)',
                ExpressionAttributeNames={
                    '#r': 'videoId'
                }
            )
        else:
            dyn_table.put_item(
                Item=job,
            )

        sqs_client.send_message(
            QueueUrl=YTMP3_DOWNLOADER_QUEUE_URL,
            MessageBody=json.dumps({'videoId': video_id}),
        )

        return job
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
            raise
        else:
            return get_download_job_from_db(video_id)


def handler(event, context):
    video_id = event['pathParameters']['videoId']
    if not video_id:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'content-type': 'application/json',
            },
            'body': json.dumps({
                'error': 'Missing videoId'
            }),
        }

    try:
        cached_result = get_download_job_from_db(video_id)
        # Redownload if file not exists in s3 and status is 'COMPLETE'
        redownload = cached_result and cached_result['status'] == 'COMPLETE' and not is_in_store(video_id)

        if cached_result and not redownload:
            # If there's a failure from the downloader, we only need to show the error
            if cached_result['status'] == 'FAILED':
                return {
                        'statusCode': 400,
                        'headers': {
                            'Access-Control-Allow-Origin': '*',
                            'content-type': 'application/json',
                        },
                        'body': json.dumps({ 'error': cached_result['error'] }),
                    }

            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'content-type': 'application/json',
                },
                'body': json.dumps(cached_result),
            }

        valid, error_message = is_video_id_valid(video_id)
        if not valid:
            # It's not valid anymore and needs deleting from the table
            if redownload:
                dyn_table.delete_item(
                    Key={
                        'videoId': video_id
                    }
                )

            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'content-type': 'application/json',
                },
                'body': json.dumps({
                    'error': error_message
                })
            }

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'content-type': 'application/json',
            },
            'body': json.dumps(put_download_job_to_queue(video_id, redownload))
        }
    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'Access-Control-Allow-Origin': '*',
            'body': json.dumps({'error': 'Internal server error'})
        }

# if __name__ == '__main__':
#     # print(is_in_store('iENAm60rSbA'))
#     print(handler({
#         'pathParameters': {
#             'videoId': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
#         }
#     }, {}))
