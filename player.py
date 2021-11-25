
import discord
from discord.ext import commands
from youtube_dl import YoutubeDL
from embed import Embed
from song_queue import SongQueue
import asyncio


FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {'default_search': 'auto','source_address': '0.0.0.0','format': 'bestaudio'}
#'format': 'bestaudio', 

ytdl = YoutubeDL(YDL_OPTIONS)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data), data







class Player:
    def __init__(self, client):
        self.client = client
        self.player = None
        self.queue = SongQueue()
        self.streamAudio = False
        
    async def connect(self, ctx, channel):
        await channel.connect()
        self.player = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        self.embed = Embed()

    async def stream(self, ctx, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        async with ctx.typing():
            # player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            player = await YTDLSource.from_url(url, loop=False, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {player.title}')

    async def get_Title(self, url):
        with YoutubeDL(YDL_OPTIONS) as ydl:
            data, video = await YTDLSource.from_url(url, loop=False, stream=True)
            print(video)
            if 'entries' in video:
                video_format = video['entries'][0]["formats"][0]
                Url = video['entries'][0]['webpage_url']
                playUrl = video_format['url']
                title = video['entries'][0]["title"]
                d = video['entries'][0]['duration']
            elif 'formats' in video:
                # video_format = video['entries'][0][0]
                # Url = video['entries'][0]['webpage_url']
                # playUrl = video_format['url']
                # title = video["title"]
                Url = video['webpage_url']
                playUrl = video['url']
                title = video["title"]
                d = video['duration']
            else:
                Url = video["webpage_url"]
                playUrl = video["webpage_url"]
                title = video["title"]
                d = video['duration']


            minutes, seconds = divmod(d, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)

            duration = ""
            if days > 0:
                duration +='{}:'.format(days)
            if hours > 0:
                duration +='{}:'.format(hours)
            if minutes > 0:
                if minutes < 10:
                    duration +='0{}:'.format(minutes)
                else:
                    duration +='{}:'.format(minutes)
            if seconds > 0:
                if seconds < 10:
                    duration +='0{}:'.format(seconds)
                else:
                    duration +='{}:'.format(seconds)

            return title, Url, playUrl, duration[:-1]

    async def play(self, url, ctx):
        with YoutubeDL(YDL_OPTIONS) as ydl:
            video = ydl.extract_info(url, download = False)
            if 'entries' in video:
                video_format = video['entries'][0]["formats"][0]
                URL = video_format["url"]
            elif 'formats' in video:
                video_format = video["formats"][0]
                URL = video_format["url"]
            else:
                URL = video["webpage_url"]
                #title = video["title"]

        player, data = await YTDLSource.from_url(url, loop=False, stream=True)
        self.player.play(player, after=lambda e: print(f'Player error: {e}') if e else None)


        await self.embed.send_playing_status(ctx, 1, await self.queue.get_queue())

        # self.player.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        while self.player.is_playing():
            await asyncio.sleep(.1)
        if not self.player.is_paused():
            queue = await self.queue.get_queue()
            await self.queue.remove_from_queue(queue[0].id)
            if len(await self.queue.get_queue()) > 0:
                #self.player.play(discord.FFmpegPCMAudio(await self.queue.get_queue[0].url, **FFMPEG_OPTIONS))
                #await self.play((await self.queue.get_queue())[0].playUrl, ctx)
                await self.play(await ydl.from_url(url, stream=True), ctx)


    async def pause(self, ctx):
        if not self.player.is_connected():
            return await ctx.send("I am not connected to a voice channel")
        if not self.player.is_playing:
            await ctx.send("There are no tracks playing")
            return
        else:
            await ctx.message.add_reaction("\U0001F44C")
        try:
            voice_channel = ctx.author.voice.channel
        except:
            await ctx.send(str(ctx.message.author.name) + " is not in a channel.")
            return
        if voice_channel != None:
            await self.embed.send_playing_status(ctx, 2, await self.queue.get_queue())    
            self.player.pause()

    async def resume(self, ctx):
        vc = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if not vc or not vc.is_connected():
            return await ctx.send("I am not connected to a voice channel")
        if not vc.is_paused():
            return await ctx.send("The track is already playing")
        else:
            await ctx.message.add_reaction("\U0001F44C")
        try:
            ctx.author.voice.channel
        except:
            return await ctx.send(str(ctx.message.author.name) + " is not in a channel.")
        await self.embed.send_playing_status(ctx, 1, await self.queue.get_queue())   
        vc.resume()

    async def stop(self, ctx):
        vc = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        vc.stop()
        await ctx.message.add_reaction("\U0001F44C")

    async def is_connected(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice == None:
            return False
        else:
            return True