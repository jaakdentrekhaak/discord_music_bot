import discord
from discord.ext import commands
import youtube_dl
import urllib.parse
import requests


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

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Ge zit ni in een voice channel se wabbe")
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)

    @commands.command()
    async def disconnect(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def play(self, ctx, *input):
        ctx.voice_client.stop()
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        YDL_OPTIONS = {
            'format': 'bestaudio'
        }
        vc = ctx.voice_client

        msg = ' '.join(input)

        if (not msg.startswith('http')):
            # Search song on YouTube
            video_id = get_video_id_from_track_name(msg)
            url = f'https://www.youtube.com/watch?v={video_id}'
        else:
            url = msg

        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
            vc.play(source)

    @commands.command()
    async def pause(self, ctx):
        await ctx.voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        await ctx.voice_client.resume()


def setup(client):
    client.add_cog(Music(client))
