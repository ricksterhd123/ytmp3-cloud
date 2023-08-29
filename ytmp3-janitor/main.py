import logging
import os
import boto3
from datetime import datetime, timedelta

logger = logging.getLogger('ytmp3-janitor')
logger.setLevel(logging.INFO)

YTMP3_DB_NAME = os.environ.get('YTMP3_DB_NAME')

YTMP3_STORE_BUCKET_NAME = os.environ.get('YTMP3_STORE_BUCKET_NAME')

if not YTMP3_DB_NAME:
    raise Exception('YTMP3_DB_NAME undefined')

if not YTMP3_STORE_BUCKET_NAME:
    raise Exception('YTMP3_STORE_BUCKET_NAME undefined')

dyn_table = boto3.resource('dynamodb').Table(YTMP3_DB_NAME)
s3_client = boto3.client('s3')
now = datetime.now()

def get_expired_videos():
    ttl_ago = (now - timedelta(hours=2)).isoformat()

    results = dyn_table.scan(
        ScanFilter={
            'updatedAt': {
                'AttributeValueList': [ttl_ago],
                'ComparisonOperator': 'LT'
            }
        }
    )

    return results.get("Items", [])

def remove_expired_videos(videos):
    video_ids = list(map(lambda video : video.get('videoId'), videos))[:1000]

    s3_client.delete_objects(
        Bucket=YTMP3_STORE_BUCKET_NAME,
        Delete={
            'Objects': list(map(lambda video_id : { 'Key': f"{video_id}.mp3" }, video_ids))
        }
    )

    with dyn_table.batch_writer() as batch:
        for video_id in video_ids:
            batch.delete_item(Key={'videoId': video_id})

def handler():
    expired_videos = get_expired_videos()
    logger.info(f"Cleaning up {len(expired_videos)} videos")
    remove_expired_videos(expired_videos)

handler()
