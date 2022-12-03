FROM public.ecr.aws/lambda/python:3.9.2022.12.02.20

COPY requirements.txt .
RUN  python3.9 -m pip install --upgrade pip
RUN  python3.9 -m pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY main.py ${LAMBDA_TASK_ROOT}

CMD [ "main.handler" ]
