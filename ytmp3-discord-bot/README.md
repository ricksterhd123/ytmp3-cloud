# ytmp3-discord-bot

## Setup
Inside `config.py` contains the bot configuration

```python
config = {
    "command_prefix": "$", # Command prefix for discord bot, e.g. $download https://...
    "log_path": "logs/ytmp3-discord-bot.log", # Path to store log files, must create directory!
    "bot_token": "###DISCORD BOT TOKEN###", # Obtained from discord developer app
    "ytmp3_api_url": "###YTMP3 API URL###" # Obtained from deploying ytmp3-cloud
}
```

- Set `bot_token` and `ytmp3_api_url`

### Bare metal
- `mkdir -p logs`
- `pip install -r requirements.txt`
- `python main.py`

### Docker
- Run the `Dockerfile``
