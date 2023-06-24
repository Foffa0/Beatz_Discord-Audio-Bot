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
from embed import PlayerEmbed, QueueEmbed
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
    'include_ads': False,
}

ytdl_channel_options = {
    'write_thumbnail': True,
    'playlist_items': 0,
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
        self.last_channel = None
        self.playerEmbed = PlayerEmbed(client=self.client, player=self)
        self.queueEmbed = QueueEmbed(client=self.client, player=self)
        self.delete_messages = []   # delete messages when the bot disconnects from the channel

    async def connect_voice_channel(self, channel):
        await channel.connect()

    async def disconnect_voice_channel(self, voice_client: discord.VoiceClient):
        await voice_client.disconnect()
        voice_client.cleanup()
        for msg in self.delete_messages:
            try:
                await msg.delete()
            except:
                pass
        self.delete_messages = []

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
        
        with YoutubeDL(ytdl_channel_options) as ydl:
            channel_info = ydl.extract_info(url=r.get('channel_url'), download=False, process=False)
        

        # with open("sample.json", "w") as outfile:
        #     json.dump(gg, outfile)

        thumbnail = None
        if r.get('thumbnails') is not None:
            thumbnail = r.get('thumbnails')[len(r.get('thumbnails')) - 1]['url']
        
        song = Song(linkutils.Origins.Default, host, title=r.get('title'), duration=r.get('duration'), url=r.get('webpage_url'), thumbnail=thumbnail, channel=r.get('uploader'), channel_thumbnail=channel_info.get('thumbnails')[0]['url'])

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

            with YoutubeDL(ytdl_channel_options) as ydl:
                channel_info = ydl.extract_info(url=r['entries'][0]['channel_url'], download=False, process=False)
            

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
                thumbnail = info.get('thumbnail')

                song = Song(linkutils.Origins.Playlist,
                            linkutils.Sites.YouTube, url=link, title=title, duration=duration, thumbnail=thumbnail, channel=info.get('uploader'), channel_thumbnail=channel_info.get('thumbnails')[0]['url'])

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
        queue_embed, queue_view = self.queueEmbed.build()

        try:
            await self.playerEmbed.msg.edit(embed=embed, view=view)
        except:
            self.playerEmbed.msg = await self.last_channel.send(embed=embed, view=view)

        try:
            await self.queueEmbed.msg.edit(embed=queue_embed, view=queue_view)
        except:
            pass

        while vc.is_playing():
            await asyncio.sleep(.1)

    async def pause(self):
        self.guild.voice_client.pause()
        embed, view = self.playerEmbed.build_embed()
        try:
            await self.playerEmbed.msg.edit(embed=embed, view=view)
        except:
            self.playerEmbed.msg = await self.last_channel.send(embed=embed, view=view)

    async def resume(self):
        self.guild.voice_client.resume()
        embed, view = self.playerEmbed.build_embed()
        try:
            await self.playerEmbed.msg.edit(embed=embed, view=view)
        except:
            self.playerEmbed.msg = await self.last_channel.send(embed=embed, view=view)

    async def skip(self, index=-1):
        if index > 0 and index < len(self.playlist.playque):
            self.playlist.skip(index)
        self.guild.voice_client.stop()
        embed, view = self.playerEmbed.build_embed()
        try:
            await self.playerEmbed.msg.edit(embed=embed, view=view)
        except:
            self.playerEmbed.msg = await self.last_channel.send(embed=embed, view=view)
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
    
