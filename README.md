# ytmp3 cloud
The cloud-based YouTube to mp3 host/converter

## Prerequisites
- bash
- wget
- docker
- awscli (with admin account)
- samcli

## Setup

Choose a unique bucket name
```bash
echo ytmp3-cloud-"$(tr -dc a-z0-9 </dev/urandom | head -c 13 ; echo '')"
```

Set `YTMP3_STORE_BUCKET_NAME` in scripts/deploy.sh

```bash
bash ./scripts/deploy.sh
```

## Destroy
```bash
bash ./scripts/destroy.sh
```

## REST API
### GET /mp3/videoId

#### 400 Invalid videoId
```json
{
    "error": "Invalid videoId"
}
```

#### 400 Download failed
```json
{
    "videoId": "#########",
    "status": "FAILED",
    "error": "Download failed, please wait 1 minute and try again",
    "updatedAt": "2023-04-23T19:27:44.850Z",
    "createdAt": "2023-04-23T19:27:44.850Z"
}
```

#### 200 Download pending
```json
{
    "videoId": "#########",
    "status": "PENDING",
    "updatedAt": "2023-04-23T19:27:44.850Z",
    "createdAt": "2023-04-23T19:27:44.850Z"
}
```

#### 200 Download complete
```json
{
    "videoId": "#########",
    "status": "COMPLETE",
    "url": "https://bpmqrjcb.s3.eu-west-2.amazonaws.com/ef8Ej3tj9bs.mp3",
    "updatedAt": "2023-04-23T19:27:44.850Z",
    "createdAt": "2023-04-23T19:27:44.850Z"
}
```
