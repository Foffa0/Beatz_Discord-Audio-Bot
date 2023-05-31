import discord
from discord import app_commands
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio
import linkutils
import concurrent.futures
from song import Song
from playlist import Playlist
from config import config
from embed import PlayerEmbed
import json
# FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
# YDL_OPTIONS = {'default_search': 'auto','source_address': '0.0.0.0','format': 'bestaudio'}
# #'format': 'bestaudio', 

# ytdl = YoutubeDL(YDL_OPTIONS)

# class YTDLError(Exception):
#     pass


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    'options': '-vn',
}

ytdl = YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, executable="D:/Dokumente/PythonProjects/AudioDiscordBot/ffmpeg/ffmpeg.exe", **ffmpeg_options), data=data)



class Player(object):
    """ Controls the playback of audio """

    def __init__(self, client: commands.Bot, guild: discord.Guild):
        self.client = client
        self.guild = guild
        #self.timer = utils.Timer(self.timeout_handler)
        self.playlist = Playlist()
        self.current_song = None
        self.playerEmbed = PlayerEmbed(client=self.client, player=self)

    async def connect_voice_channel(self, channel):
        await channel.connect()

    async def disconnect_voice_channel(self, voice_client: discord.VoiceClient):
        await voice_client.disconnect()

    async def add_song(self, track):
        host = linkutils.identify_url(track)
        is_playlist = linkutils.identify_playlist(track)

        if is_playlist != linkutils.Playlist_Types.Unknown:
            count, title = await self.add_Playlist(is_playlist, track)
            return self.playerEmbed.generalEmbed(config.EMBED_QUEUE_ADD_TITLE + str(count) + " tracks.", "from playlist: " + title), None
        
        if host == linkutils.Sites.Unknown:
            if linkutils.get_url(track) is not None:
                return None

            #track = self.search_youtube(track)

        if host == linkutils.Sites.Spotify:
            track = await linkutils.convert_spotify(track)

        if host == linkutils.Sites.YouTube:
            track = track.split("&list=")[0]


        try:
            r = ytdl.extract_info(
                track, download=False)
        except Exception as e:
            if "ERROR: Sign in to confirm your age" in str(e):
                return None
            
        if 'entries' in r:
            # take first item from a playlist
            r = r['entries'][0]

        thumbnail = None
        if r.get('thumbnails') is not None:
            thumbnail = r.get('thumbnails')[len(r.get('thumbnails')) - 1]['url']

        song = Song(linkutils.Origins.Default, host, title=r.get('title'), duration=r.get('duration'), url=r.get('webpage_url'), thumbnail=thumbnail)

        self.playlist.add(song)
        if self.current_song == None:
            print("Playing {}".format(track))
            self.current_song = self.playlist.playque[0]
            #await self.play(self.playlist.playque[0])
            coro = self.play(self.playlist.playque[0])
            self.client.loop.create_task(coro)
            return self.playerEmbed.build_embed()
        else: 
            return self.playerEmbed.generalEmbed(config.EMBED_QUEUE_ADD_TITLE + song.title), None

    

    async def add_Playlist(self, playlist_type, url):
        if playlist_type == linkutils.Playlist_Types.YouTube_Playlist:
            if ("playlist?list=" in url):
                listid = url.split('=')[1]
            else:
                video = url.split('&')[0]
                await self.add_song(video)
                return
            r = await self.client.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            with open('convert.txt', 'w') as convert_file:
                convert_file.write(json.dumps(r))
            #r = ytdl.extract_info(url, download=False)
            for entry in r['entries']:
                if entry == None:
                    continue
                link = "https://www.youtube.com/watch?v={}".format(entry['id'])
                
                info = ytdl.extract_info(
                link, download=False)
                #song.url = r.get('url')
                title = info.get('title')
                duration = info.get('duration')
                url = info.get('webpage_url')
                thumbnail = info.get('thumbnails')[0]['url']

                song = Song(linkutils.Origins.Playlist,
                            linkutils.Sites.YouTube, url=link, title=title, duration=duration, thumbnail=thumbnail)

                self.playlist.add(song)
            if self.current_song == None:
                self.current_song = self.playlist.playque[0]
                coro = self.play(self.playlist.playque[0])
                self.client.loop.create_task(coro)
                # coro = self.play(self.playlist.playque[0])
                # self.client.loop.create_task(coro)
            return len(r['entries']), r.get('title')

        if playlist_type == linkutils.Playlist_Types.Spotify_Playlist:
            links = await linkutils.get_spotify_playlist(url)
            for link in links:
                song = Song(linkutils.Origins.Playlist,
                            linkutils.Sites.Spotify, webpage_url=link)
                self.playlist.add(song)

        if playlist_type == linkutils.Playlist_Types.BandCamp_Playlist:
            r = ytdl.extract_info(url, download=False)

            for entry in r['entries']:

                link = entry.get('url')

                song = Song(linkutils.Origins.Playlist,
                            linkutils.Sites.Bandcamp, webpage_url=link)

                self.playlist.add(song)

        #for song in list(self.playlist.playque)[:config.MAX_SONG_PRELOAD]:
        #    asyncio.ensure_future(self.preload(song))

    async def preload(self, song: Song): #! not needed!?

        if song.title != None:
            return

        def down(song: Song):

            if song.host == linkutils.Sites.Spotify:
                song.url = self.search_youtube(song.title)

            if song.url == None:
                return None
            
            r = ytdl.extract_info(
                song.url, download=False)
            #song.url = r.get('url')
            song.title = r.get('title')
            song.duration = r.get('duration')
            song.url = r.get('webpage_url')
            song.thumbnail = r.get('thumbnails')[0]['url']
            #print(song.title)

        if song.host == linkutils.Sites.Spotify:
            song.title = await linkutils.convert_spotify(song.info.webpage_url)

        loop = self.client.loop#asyncio.get_event_loop()
        executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=config.MAX_SONG_PRELOAD)
        await asyncio.wait(fs={loop.run_in_executor(executor, down, song)}, return_when=asyncio.ALL_COMPLETED)

    
    def next_song(self):
        """Invoked after a song is finished. Plays the next song from playlist."""

        if self.current_song == -1:
            next_song = self.playlist.prev()
        else:
            next_song = self.playlist.next()

        if next_song is None:
            self.current_song = None
            return

        coro = self.play(next_song)
        self.client.loop.create_task(coro)

    async def play(self, song:Song):
        self.current_song = self.playlist.playque[0]
        print("Playque:")
        for song1 in self.playlist.playque:
            print(song1.title)
        print("playhistory:")
        for song2 in self.playlist.playhistory:
            print(song2.title)
                

        player = await YTDLSource.from_url(song.url, loop=self.client.loop)
        vc = self.guild.voice_client
        vc.play(player, after=lambda e: self.next_song())
        embed, view = self.playerEmbed.build_embed()
        await self.playerEmbed.msg.edit(embed=embed, view=view)
        while vc.is_playing():
            await asyncio.sleep(.1)

    async def pause(self):
        self.guild.voice_client.pause()

    async def resume(self):
        self.guild.voice_client.resume()

    async def skip(self):
        self.guild.voice_client.stop()
        #self.next_song()

    async def previous(self):
        if not len(self.playlist.playhistory) < 1:
            self.current_song = -1
            self.guild.voice_client.stop()
        #self.next_song(True)

    async def clear(self):
        self.playlist.clear()

    def is_playing(self):
        if self.guild.voice_client.is_playing():
            return True
        return False
    
    def is_paused(self):
        if self.guild.voice_client.is_paused():
            return True
        return False
    

















# import discord
# from discord.ext import commands
# from youtube_dl import YoutubeDL
# from embed import Embed
# from song_queue import SongQueue
# import asyncio

# FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
# YDL_OPTIONS = {'default_search': 'auto','source_address': '0.0.0.0','format': 'bestaudio'}
# #'format': 'bestaudio', 

# ytdl = YoutubeDL(YDL_OPTIONS)

# class YTDLError(Exception):
#     pass

# class YTDLSource(discord.PCMVolumeTransformer):
#     def __init__(self, source, *, data, volume=0.5):
#         super().__init__(source, volume)

#         self.data = data

#         self.title = data.get('title')
#         self.url = data.get('url')

#     @classmethod
#     async def from_url(cls, url, *, loop=None, stream=False):
#         loop = loop or asyncio.get_event_loop()
#         data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

#         if 'entries' in data:
#             # take first item from a playlist
#             data = data['entries'][0]

#         filename = data['url'] if stream else ytdl.prepare_filename(data)
#         return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)


# # class YTDLSource(discord.PCMVolumeTransformer):
# #     def __init__(self, source, *, data, volume=0.5):
# #         super().__init__(source, volume)

# #         self.data = data

# #         self.title = data.get('title')
# #         self.url = data.get('url')

# #     @classmethod
# #     async def from_url(cls, url, *, loop=None, stream=True):
# #         loop = loop or asyncio.get_event_loop()
# #         data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

# #         if data is None:
# #             raise YTDLError('Couldn\'t fetch `{}`'.format(url))

# #         if 'entries' in data:
# #             # take first item from a playlist
# #             data = data['entries'][0]

# #         filename = data['url'] if stream else ytdl.prepare_filename(data)
# #         return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data), data



# # class Player:
# #     def __init__(self, client):
# #         self.client = client
# #         self.voiceClient = None
# #         self.queue = SongQueue()
# #         self.streamAudio = False
# #         self.stopped = False
        
# #     async def connect(self, ctx, channel):
# #         await channel.connect()
# #         self.voiceClient = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
# #         self.embed = Embed()

# #     async def extract_data(self, data):
# #         '''extract the data from a dict
        
# #         Parameters
# #         ----------
# #         data: :class:`dict`
# #             The video data from the player
            
# #         Returns
# #         --------
# #         title: :class:`str`
# #             The title of the video
# #         Url: :class:`str`
# #             The url to the video witch the user enter into the browser
# #         playUrl: :class:`str`
# #             The stream url for the player
# #         duration: :class:`str`
# #             The duration of the video
# #         '''
# #         if 'entries' in data:
# #             video_format = data['entries'][0]["formats"][0]
# #             Url = data['entries'][0]['webpage_url']
# #             playUrl = video_format['url']
# #             title = data['entries'][0]["title"]
# #             d = data['entries'][0]['duration']
# #         elif 'formats' in data:
# #             # video_format = video['entries'][0][0]
# #             # Url = video['entries'][0]['webpage_url']
# #             # playUrl = video_format['url']
# #             # title = video["title"]
# #             Url = data['webpage_url']
# #             playUrl = data['url']
# #             title = data["title"]
# #             d = data['duration']
# #         else:
# #             Url = data["webpage_url"]
# #             playUrl = data["webpage_url"]
# #             title = data["title"]
# #             d = data['duration']


# #         minutes, seconds = divmod(d, 60)
# #         hours, minutes = divmod(minutes, 60)
# #         days, hours = divmod(hours, 24)

# #         duration = ""
# #         if days > 0:
# #             duration +='{}:'.format(days)
# #         if hours > 0:
# #             duration +='{}:'.format(hours)
# #         if minutes > 0:
# #             if minutes < 10:
# #                 duration +='0{}:'.format(minutes)
# #             else:
# #                 duration +='{}:'.format(minutes)
# #         if seconds > 0:
# #             if seconds < 10:
# #                 duration +='0{}:'.format(seconds)
# #             else:
# #                 duration +='{}:'.format(seconds)

# #         return title, Url, playUrl, duration[:-1]

# #     async def addSong(self, url, ctx):
# #         '''Adds the song to the queue if the bot is already playing

# #         Parameters
# #         ----------- 
# #         url: :class:`str`
# #             The url to the youtube video
# #         ctx: :class:`Context` 
# #             The ctx of the command currently being invoked.'''

# #         player, data = await YTDLSource.from_url(url, loop=False, stream=True)

# #         if not await self.is_connected(ctx):
# #             await self.connect(ctx, ctx.author.voice.channel)
# #             songTitle, songUrl, playUrl, duration = await self.extract_data(data)
# #             await self.queue.add_to_queue(songTitle, songUrl, playUrl, duration, player)
# #             await self.play(url,ctx,player)

# #         elif len(await self.queue.get_queue()) == 0:
# #             Title, Url, playUrl, duration = await self.extract_data(data)
# #             await self.queue.add_to_queue(Title, Url, playUrl, duration, player)
# #             await self.play(playUrl, ctx, player)
# #         else:
# #             Title, Url, playUrl, duration = await self.extract_data(data)
# #             await self.queue.add_to_queue(Title, Url, playUrl, duration, player)
# #             await self.embed.send_playing_status(self.client, ctx, 3, await self.queue.get_queue())

# #     async def play(self, url, ctx, player):
# #         '''Streams from a url (same as yt, but doesn't predownload)
# #         Parameters
# #         ----------- 
# #         url: :class:`str`
# #             The url to the youtube video
# #         ctx: :class:`Context` 
# #             The ctx of the command currently being invoked.'''

# #         try:
# #             self.voiceClient.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
# #         except:
# #             self.voiceClient.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

# #         await self.embed.send_playing_status(self.client, ctx, 1, await self.queue.get_queue())
# #         self.stopped = False
# #         # self.player.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
# #         while self.voiceClient.is_playing():
# #             await asyncio.sleep(.1)
# #         if not self.voiceClient.is_paused() and not self.stopped:
# #             queue = await self.queue.get_queue()
# #             await self.queue.remove_from_queue(queue[0].id)
# #             if len(await self.queue.get_queue()) > 0:
# #                 #self.player.play(discord.FFmpegPCMAudio(await self.queue.get_queue[0].url, **FFMPEG_OPTIONS))
# #                 #await self.play((await self.queue.get_queue())[0].playUrl, ctx)
# #                 await self.play((await self.queue.get_queue())[0].playUrl, ctx, (await self.queue.get_queue())[0].player)


# #     async def pause(self, ctx):
# #         if not self.voiceClient.is_connected():
# #             return await ctx.send("I am not connected to a voice channel", delete_after = 10.0)
# #         if not self.voiceClient.is_playing:
# #             await ctx.send("There are no tracks playing", delete_after = 10.0)
# #             return
       
# #         try:
# #             voice_channel = ctx.author.voice.channel
# #         except:
# #             await ctx.send(str(ctx.message.author.name) + " is not in a channel.", delete_after = 10.0)
# #             return
# #         if voice_channel != None:
# #             await self.embed.send_playing_status(self.client, ctx, 2, await self.queue.get_queue())    
# #             self.voiceClient.pause()

# #     async def resume(self, ctx):
# #         vc = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
# #         if not vc or not vc.is_connected():
# #             return await ctx.send("I am not connected to a voice channel", delete_after = 10.0)
# #         if not vc.is_paused():
# #             return await ctx.send("The track is already playing", delete_after = 10.0)
# #         try:
# #             ctx.author.voice.channel
# #         except:
# #             return await ctx.send(str(ctx.message.author.name) + " is not in a channel.", delete_after = 10.0)
# #         #await self.embed.send_playing_status(self.client, ctx, 1, await self.queue.get_queue())   
# #         vc.resume()

# #     async def stop(self, ctx, clearQueue=True):
# #         self.stopped = True
# #         self.voiceClient.stop()
# #         if clearQueue:
# #             await self.queue.clear_queue()

# #     async def is_connected(self, ctx):
# #         voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
# #         if voice == None:
# #             return False
# #         else:
# #             return True

# #     async def disconnect(self, ctx):
# #         await self.embed.disconnect(ctx)

# #     async def play_from_dm_command(self, guild_id, channel, url):
# #         player, data = await YTDLSource.from_url(url, loop=False, stream=True)
# #         #guild = self.client.get_guild(guild_id)
# #         for guild_ in self.client.guilds:
# #             if guild_.id == guild_id:
# #                 guild = guild_
# #                 break
# #         voice = discord.utils.get(guild.voice_channels, id=channel)
# #         voiceClient = discord.utils.get(self.client.voice_clients, guild=guild)
# #         if voiceClient == None:
# #             await voice.connect()
# #         await voiceClient.play(player, after=await voice.disconnect())