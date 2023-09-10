import re
import requests
import asyncio
import logger
import discord

from config import config
from discord.ext import tasks, commands

logging = logger.get_logger(config["log_path"])
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=config["command_prefix"], intents=intents)

class Ytmp3(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.ytmp3_api_url = config["ytmp3_api_url"]
        self.download_queue = {}

    def __get_youtube_video_id(self, video_url):
        """
        Nice way to validate and extract youtube video id
        https://gist.github.com/brunodles/927fd8feaaccdbb9d02b
        """
        m = re.search("(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?", video_url)
        return False if m is None else m.group(1)

    def __get_video(self, video_id):
        """
        Calls the `GET /mp3` endpoint of ytmp3 and return the response
        """
        try:
            r = requests.get(f"{self.ytmp3_api_url}/mp3/{video_id}")
            if r.status_code >= 500:
                return None, "Server error"
            response = r.json()
            if r.status_code == 400:
                return None, response.get("error", "")
            return response, None
        except Exception as error:
            logging.error(error)
        return None, "Server error"

    def cog_load(self):
        self.update.start()

    def cog_unload(self):
        self.update.cancel()

    @tasks.loop(seconds=5.0)
    async def update(self):
        """
        Process job on download queue 1 at a time:
        if job status 'COMPLETE', pop job off queue and respond back to each ctx
        if job fails 4xx or 5xx, pop job off queue and respond back to each ctx
        """
        jobs = self.download_queue.copy()
        for video_id, ctxs in jobs.items():
            video, error = self.__get_video(video_id)
            if not video:
                self.download_queue.pop(video_id)
                for ctx in ctxs:
                    await ctx.reply(f"Error: {error}")
                continue

            status = video.get("status")
            logging.info(f"video_id: {video_id}, status: {status}")

            if status == "COMPLETE":
                self.download_queue.pop(video_id)
                url = video.get("url", "Oops something went wrong")
                for ctx in ctxs:
                    await ctx.reply(f"{url}")

    @commands.command()
    async def download(self, ctx, video_url):
        if not ctx.guild:
            return

        video_id = self.__get_youtube_video_id(video_url)
        if not video_id:
            await ctx.reply(f"Error: Invalid YouTube URL")
            return

        if not self.download_queue.get(video_id):
            self.download_queue[video_id] = []

        self.download_queue[video_id].append(ctx)

ytmp3 = Ytmp3(bot, config)

@bot.event
async def on_ready():
    logging.info('We have logged in as {0}'.format(bot))
    ytmp3.cog_load()

def main(config):
    asyncio.run(bot.add_cog(ytmp3))
    bot.run(config["bot_token"])

if __name__ == '__main__':
    main(config)
