import asyncio
import discord
from discord.ext import commands
import youtube_dl
import urllib.parse
import requests
import time
import threading

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
YDL_OPTIONS = {
    'format': 'bestaudio'
}
MAX_TIMER = 15


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


def get_track_name_from_video_url(url: str) -> str:
    """Retrieve the track name given the YouTube URL of a song

    Args:
        url (str): YouTube URL of song

    Returns:
        str: track name of song with given URL
    """
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['title']


class Music(commands.Cog):
    def __init__(self, client) -> None:
        self.client = client
        self.queue: list = []
        self.timer: int = MAX_TIMER

    @commands.command()
    async def join(self, ctx):
        """Let bot join the voice channel you're in"""
        if ctx.author.voice is None:
            await ctx.send("You're not in a voice channel")
        else:
            voice_channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await voice_channel.connect()
            else:
                await ctx.voice_client.move_to(voice_channel)

            # Start thread for listening for song requests
            threading.Thread(target=asyncio.run, args=(
                self.listen_for_songs(ctx),)).start()

    @commands.command()
    async def stop(self, ctx):
        """Disconnect bot from voice channel"""
        self.queue = []
        await ctx.voice_client.disconnect()

    async def play_song(self, ctx, url):
        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source)

    async def listen_for_songs(self, ctx):
        while ctx.voice_client and ctx.voice_client.is_connected():
            if (not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused() and len(self.queue) > 0):
                url = self.queue.pop(0)
                await self.play_song(ctx, url)
            else:
                # # If bot is not playing a song for a few minutes, leave channel
                # if not ctx.voice_client.is_playing():
                #     self.timer -= 3
                #     if self.timer <= 0:
                #         await ctx.voice_client.disconnect()
                # else:
                #     self.timer = MAX_TIMER
                time.sleep(3)

    @commands.command()
    async def play(self, ctx, *input):
        """Play song with the given title or url"""
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
            # remove other possible parameters after ?v=...
            url = msg.split('&')[0]

        # If playlist URL is given: add all songs from playlist to queue
        if 'playlist' in url:
            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                entries = info['entries']

            for entry in entries:
                video_id = entry['id']
                self.queue.append(
                    f'https://www.youtube.com/watch?v={video_id}')
        else:
            # Add song to the queue
            self.queue.append(url)
        await ctx.send('Added to queue: ' + url)

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song"""
        ctx.voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        """Resumes the current song if paused"""
        ctx.voice_client.resume()

    @commands.command()
    async def skip(self, ctx):
        """Skips the current song"""
        ctx.voice_client.stop()

    @commands.command()
    async def queue(self, ctx):
        """Shows the current queue"""
        result = ''
        for i in range(len(self.queue)):
            result += f'{i+1}: {get_track_name_from_video_url(self.queue[i])}\n'
        await ctx.send(result if len(result) > 0 else 'Nothing in the queue')

    @commands.command()
    async def rm(self, ctx, index):
        """Remove song with index from queue"""
        try:
            ind = int(index) - 1
            self.queue.pop(ind)
        except:
            await ctx.send('Given index is not valid')


def setup(client):
    client.add_cog(Music(client))
