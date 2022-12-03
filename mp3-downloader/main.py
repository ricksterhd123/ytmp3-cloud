import logging
import boto3
from botocore.exceptions import ClientError
import os
from yt_dlp import YoutubeDL

logger = logging.getLogger('mp3-downloader')
logger.setLevel(logging.INFO)

BUCKET_NAME = os.environ.get('BUCKET_NAME')
if not BUCKET_NAME:
    raise Exception("Expected BUCKET_NAME environment variable but got None")

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def handler(event, context):
    url = event.get('url')

    if not url:
        raise Exception("No url provided")

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

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.sanitize_info(ydl.extract_info(url, download=False))
        video_id = info_dict.get("display_id", None)
        duration = info_dict.get("duration", None)
        file_name = f"{video_id}.mp3"

        logger.info(f"Video ID: {video_id}, Duration: {duration}")

        if not duration:
            logger.warning(f"Video ID: {video_id} has no duration metadata")
            logger.error("Cannot find duration in metadata. Are you sure this is a YouTube video?")
            return

        ydl.download([url])
        upload_file(f"{file_path}/{file_name}", BUCKET_NAME, file_name)

if __name__ == '__main__':
    handler({
        "url": "https://www.youtube.com/watch?v=OhILMI3mQ5I"
    }, {})
