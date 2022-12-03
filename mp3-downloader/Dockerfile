FROM public.ecr.aws/lambda/python:3.9

## Build ffmpeg
COPY bin/ffmpeg /usr/local/bin/
COPY bin/ffprobe /usr/local/bin/

# Setup app
WORKDIR /app
COPY requirements.txt .
RUN python3.9 -m pip install --upgrade pip
RUN python3.9 -m pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY main.py ${LAMBDA_TASK_ROOT}

CMD [ "main.handler" ]
