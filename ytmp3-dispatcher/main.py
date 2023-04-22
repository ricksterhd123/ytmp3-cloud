import json
from yt_dlp import YoutubeDL
import logging

logger = logging.getLogger('ytmp3-dispatcher')
logger.setLevel(logging.INFO)


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
        'body': json.dumps(event)
    }


# if __name__ == '__main__':
#     handler({
#         'pathParameters': {
#             'videoId': 'hbQpP8y16Fk'
#         }
#     }, {})
