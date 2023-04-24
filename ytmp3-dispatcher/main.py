import json
import logging
import boto3
import botocore
import os
from datetime import datetime
from yt_dlp import YoutubeDL

logger = logging.getLogger('ytmp3-dispatcher')
logger.setLevel(logging.INFO)

MAX_VIDEO_DURATION_MINS = 90
YTMP3_DOWNLOADER_QUEUE_URL = os.environ.get('YTMP3_DOWNLOADER_QUEUE_URL')
YTMP3_DB_NAME = os.environ.get('YTMP3_DB_NAME')

if not YTMP3_DOWNLOADER_QUEUE_URL:
    raise Exception("YTMP3_DOWNLOADER_QUEUE_URL undefined")

if not YTMP3_DB_NAME:
    raise Exception("YTMP3_DB_NAME undefined")

sqs_client = boto3.client('sqs')
dyn_table = boto3.resource('dynamodb').Table(YTMP3_DB_NAME)


def is_video_id_valid(video_id):
    # This prevents injecting extra query parameters in the url
    # and remove nasties like &list=
    if "&" in video_id:
        return False, "Invalid videoId"

    ydl_opts = {
        "format": "bestaudio/best"
    }

    url = f"https://youtube.com/watch?v={video_id}"

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.sanitize_info(
            ydl.extract_info(url, download=False)
        )

        duration = info_dict.get("duration", None)
        if not duration:
            return False, "No duration in metadata"

        if duration > MAX_VIDEO_DURATION_MINS * 60:
            return False, f"Video exceeds {MAX_VIDEO_DURATION_MINS} minutes"

    return True, None


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


def put_download_job_to_queue(video_id):
    try:
        job = {
            'videoId': video_id,
            'status': 'PENDING',
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat()
        }

        dyn_table.put_item(
            Item=job,
            ConditionExpression="attribute_not_exists(#r)",
            # ExpressionAttributeValues={
            #     ':failedStatus': 'FAILED',
            #     ':completeStatus': 'COMPLETE'
            # },
            ExpressionAttributeNames={
                # "#status": "status",
                "#r": "videoId"
            }
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
                'content-type': 'application/json',
            },
            'body': json.dumps({
                'error': 'Missing videoId'
            }),
        }

    try:
        cached_result = get_download_job_from_db(video_id)
        if cached_result:
            return {
                'statusCode': 200,
                'headers': {
                    'content-type': 'application/json',
                },
                'body': json.dumps(cached_result),
            }

        valid, error_message = is_video_id_valid(video_id)
        if not valid:
            return {
                'statusCode': 400,
                'headers': {
                    'content-type': 'application/json',
                },
                'body': json.dumps({
                    'error': error_message
                })
            }

        return {
            'statusCode': 200,
            'headers': {
                'content-type': 'application/json',
            },
            'body': json.dumps(put_download_job_to_queue(video_id))
        }
    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

# if __name__ == '__main__':
#     print(handler({
#         'pathParameters': {
#             'videoId': 'iENAm60rSbA'
#         }
#     }, {}))
