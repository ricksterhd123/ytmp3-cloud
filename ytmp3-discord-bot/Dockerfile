FROM python:3

WORKDIR /ytmp3-discord-bot

COPY . .
RUN mkdir -p logs
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "main.py" ]
