import asyncio
import discord
from discord.ext import commands
import youtube_dl
import urllib.parse
import requests
import time
import threading


def get_video_id_from_track_name(track_name: str) -> str:
    """Retrieve the video id from the song for which the name is given in the input.

    Args:
        track_name (str): string to search on YouTube

    Returns:
        str: video id for the songs for which the name is given in the input
    """
    prefix = '"videoId":"'  # Prefix to search in server response
    query = urllib.parse.quote_plus(track_name)
    response = requests.get(
        f'https://www.youtube.com/results?search_query={query}')
    raw_body_str = response.text
    cut = raw_body_str.split(prefix)[1]
    video_id = cut.split('"')[0]

    return video_id


class Music(commands.Cog):
    def __init__(self, client) -> None:
        self.client = client
        self.queue = []

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Ge zit ni in een voice channel se wabbe")
        else:
            voice_channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await voice_channel.connect()
            else:
                await ctx.voice_client.move_to(voice_channel)

    @commands.command()
    async def disconnect(self, ctx):
        self.queue = []
        await ctx.voice_client.disconnect()

    @commands.command()
    async def stop(self, ctx):
        await self.disconnect(ctx)

    async def play_song(self, ctx, url):
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        YDL_OPTIONS = {
            'format': 'bestaudio'
        }
        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source)

    async def play_next_song(self, ctx):
        while ctx.voice_client and ctx.voice_client.is_connected():
            if (not ctx.voice_client.is_playing() and len(self.queue) > 0):
                url = self.queue.pop(0)
                await self.play_song(ctx, url)
            else:
                time.sleep(1)

    @commands.command()
    async def play(self, ctx, *input):
        # If the bot is not yet connected to the voice channel, connect it
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.join(ctx)

        # Process user input: can be URL or search query
        msg = ' '.join(input)

        if (not msg.startswith('http')):
            # Search song on YouTube
            video_id = get_video_id_from_track_name(msg)
            url = f'https://www.youtube.com/watch?v={video_id}'
        else:
            url = msg

        # Add song to the queue
        self.queue.append(url)

        # If no song is currently playing, call the play function
        if not ctx.voice_client.is_playing():
            threading.Thread(target=asyncio.run, args=(
                self.play_next_song(ctx),)).start()

    @commands.command()
    async def pause(self, ctx):
        await ctx.voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        await ctx.voice_client.resume()


def setup(client):
    client.add_cog(Music(client))
