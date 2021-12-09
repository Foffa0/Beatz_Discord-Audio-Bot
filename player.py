
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

class YTDLError(Exception):
    pass


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

        if data is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(url))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data), data



class Player:
    def __init__(self, client):
        self.client = client
        self.voiceClient = None
        self.queue = SongQueue()
        self.streamAudio = False
        self.stopped = False
        
    async def connect(self, ctx, channel):
        await channel.connect()
        self.voiceClient = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        self.embed = Embed()

    async def extract_data(self, data):
        '''extract the data from a dict
        
        Parameters
        ----------
        data: :class:`dict`
            The video data from the player
            
        Returns
        --------
        title: :class:`str`
            The title of the video
        Url: :class:`str`
            The url to the video witch the user enter into the browser
        playUrl: :class:`str`
            The stream url for the player
        duration: :class:`str`
            The duration of the video
        '''
        if 'entries' in data:
            video_format = data['entries'][0]["formats"][0]
            Url = data['entries'][0]['webpage_url']
            playUrl = video_format['url']
            title = data['entries'][0]["title"]
            d = data['entries'][0]['duration']
        elif 'formats' in data:
            # video_format = video['entries'][0][0]
            # Url = video['entries'][0]['webpage_url']
            # playUrl = video_format['url']
            # title = video["title"]
            Url = data['webpage_url']
            playUrl = data['url']
            title = data["title"]
            d = data['duration']
        else:
            Url = data["webpage_url"]
            playUrl = data["webpage_url"]
            title = data["title"]
            d = data['duration']


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

    async def addSong(self, url, ctx):
        '''Adds the song to the queue if the bot is already playing

        Parameters
        ----------- 
        url: :class:`str`
            The url to the youtube video
        ctx: :class:`Context` 
            The ctx of the command currently being invoked.'''

        player, data = await YTDLSource.from_url(url, loop=False, stream=True)

        if not await self.is_connected(ctx):
            await self.connect(ctx, ctx.author.voice.channel)
            songTitle, songUrl, playUrl, duration = await self.extract_data(data)
            await self.queue.add_to_queue(songTitle, songUrl, playUrl, duration, player)
            await self.play(url,ctx,player)

        elif len(await self.queue.get_queue()) == 0:
            Title, Url, playUrl, duration = await self.extract_data(data)
            await self.queue.add_to_queue(Title, Url, playUrl, duration, player)
            await self.play(playUrl, ctx, player)
        else:
            Title, Url, playUrl, duration = await self.extract_data(data)
            await self.queue.add_to_queue(Title, Url, playUrl, duration, player)
            await self.embed.send_playing_status(self.client, ctx, 3, await self.queue.get_queue())

    async def play(self, url, ctx, player):
        '''Streams from a url (same as yt, but doesn't predownload)
        Parameters
        ----------- 
        url: :class:`str`
            The url to the youtube video
        ctx: :class:`Context` 
            The ctx of the command currently being invoked.'''

        try:
            self.voiceClient.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
        except:
            self.voiceClient.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await self.embed.send_playing_status(self.client, ctx, 1, await self.queue.get_queue())
        self.stopped = False
        # self.player.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        while self.voiceClient.is_playing():
            await asyncio.sleep(.1)
        if not self.voiceClient.is_paused() and not self.stopped:
            queue = await self.queue.get_queue()
            await self.queue.remove_from_queue(queue[0].id)
            if len(await self.queue.get_queue()) > 0:
                #self.player.play(discord.FFmpegPCMAudio(await self.queue.get_queue[0].url, **FFMPEG_OPTIONS))
                #await self.play((await self.queue.get_queue())[0].playUrl, ctx)
                await self.play((await self.queue.get_queue())[0].playUrl, ctx, (await self.queue.get_queue())[0].player)


    async def pause(self, ctx):
        if not self.voiceClient.is_connected():
            return await ctx.send("I am not connected to a voice channel", delete_after = 10.0)
        if not self.voiceClient.is_playing:
            await ctx.send("There are no tracks playing", delete_after = 10.0)
            return
        else:
            await ctx.message.add_reaction("\U0001F44C")
        try:
            voice_channel = ctx.author.voice.channel
        except:
            await ctx.send(str(ctx.message.author.name) + " is not in a channel.", delete_after = 10.0)
            return
        if voice_channel != None:
            await self.embed.send_playing_status(self.client, ctx, 2, await self.queue.get_queue())    
            self.voiceClient.pause()

    async def resume(self, ctx):
        vc = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if not vc or not vc.is_connected():
            return await ctx.send("I am not connected to a voice channel", delete_after = 10.0)
        if not vc.is_paused():
            return await ctx.send("The track is already playing", delete_after = 10.0)
        else:
            await ctx.message.add_reaction("\U0001F44C")
        try:
            ctx.author.voice.channel
        except:
            return await ctx.send(str(ctx.message.author.name) + " is not in a channel.", delete_after = 10.0)
        #await self.embed.send_playing_status(self.client, ctx, 1, await self.queue.get_queue())   
        vc.resume()

    async def stop(self, ctx, clearQueue=True):
        self.stopped = True
        self.voiceClient.stop()
        if clearQueue:
            await self.queue.clear_queue()
        await ctx.message.add_reaction("\U0001F44C")

    async def is_connected(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice == None:
            return False
        else:
            return True

    async def disconnect(self, ctx):
        await self.embed.disconnect(ctx)

    async def play_from_dm_command(self, guild_id, channel, url):
        player, data = await YTDLSource.from_url(url, loop=False, stream=True)
        #guild = self.client.get_guild(guild_id)
        for guild_ in self.client.guilds:
            if guild_.id == guild_id:
                guild = guild_
                break
        voice = discord.utils.get(guild.voice_channels, id=channel)
        voiceClient = discord.utils.get(self.client.voice_clients, guild=guild)
        if voiceClient == None:
            await voice.connect()
        await voiceClient.play(player, after=await voice.disconnect())