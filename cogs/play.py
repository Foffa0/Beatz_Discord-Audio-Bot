import discord
from discord import app_commands
from discord.ext import commands
#from youtube_dl import YoutubeDL
from yt_dlp import YoutubeDL
import asyncio
import utils
from player import Player
from config import config

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
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
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


     

class Play(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        #self.player = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("Play cog loaded.")

    @commands.command()
    async def sync(self, ctx) -> None:
        fmt = await ctx.bot.tree.sync()
        await ctx.send(f"Synced {len(fmt)} commands.")
   

    @app_commands.command(name="test", description="Simple Testmessage")
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("This is a test message.")


    @app_commands.command(name="play", description="Play a song from YouTube")
    async def play(self, interaction: discord.Interaction, url: str):
        """Plays a file from youtube"""
        channel = interaction.channel
        user_voice = interaction.user.voice

        if utils.get_guildplayer(interaction.guild) == None:
            #utils.guild_players[interaction.guild] = Player(self.client, interaction.guild)
            utils.setGuildPlayer(interaction.guild, Player(self.client, interaction.guild))
        player: Player = utils.get_guildplayer(interaction.guild)

        if not interaction.user.voice:
            await interaction.response.send_message("You are not in a voice channel!")
            return
        else:
            bot_voice = interaction.guild.voice_client

        if bot_voice:
            # we're in a channel already
            if not bot_voice.channel.id == user_voice.channel.id:
                # move channels now - we're in VC but not the user's VC
                await bot_voice.move_to(user_voice.channel)
                await interaction.response.send_message("Moved to your channel", ephemeral=True)
        else:
            await player.connect_voice_channel(user_voice.channel)

        await interaction.response.send_message(embed=player.playerEmbed.generalEmbed(config.EMBED_SEARCH_TITLE + f" {url}", config.EMBED_SEARCH_DESCRIPTION), silent=True)
        embed, view = await player.add_song(url)
        msg = await channel.send(embed=embed, view=view, silent=True)
        await interaction.delete_original_response()
        player.playerEmbed.msg = msg
        # await interaction.response.send_message(embed=embed, view=view)
        # self.client.loop.create_task(coro)



    @app_commands.command(name="pause", description="Pause the player")
    async def pause(self, interaction: discord.Interaction):
        """Pauses the guild's player"""
        player: Player = utils.get_guildplayer(interaction.guild)
        if not player == None:
            if not player.is_playing() or player.is_paused():
                await interaction.response.send_message(content="Player already paused!", delete_after=15)
                return
            await player.pause()
            await interaction.response.send_message(content="Paused")
            return
        await interaction.response.send_message("I am not connected to a voice channel!", ephemeral=True)
        
    @app_commands.command(name="resume", description="Resume the player")
    async def resume(self, interaction: discord.Interaction):
        """Resumes the guild's player"""
        player: Player = utils.get_guildplayer(interaction.guild)
        if not player == None:
            if player.is_playing() or not player.is_paused():
                await interaction.response.send_message(content="Player already playing!", delete_after=15)
                return
            await player.resume()
            await interaction.response.send_message(content="Resumed")
            return
        await interaction.response.send_message("I am not in a voice channel", ephemeral=True, delete_after=30)

    @app_commands.command(name="skip", description="Skip to the next song in que")
    async def skip(self, interaction: discord.Interaction):
        """Skips the current song"""
        player: Player = utils.get_guildplayer(interaction.guild)
        if not player == None:
            await player.skip()
            await interaction.response.send_message("Skipped to the next song", delete_after=30)
        else:
            await interaction.response.send_message("I am not connected to a voice channel!", ephemeral=True)

    @app_commands.command(name="previous", description="Play the previous song")
    async def previous(self, interaction: discord.Interaction):
        """Play the previous song (in playhistory)"""
        player: Player = utils.get_guildplayer(interaction.guild)
        if not player == None:
            await player.previous()
            await interaction.response.send_message("PLaying previous song", delete_after=30)
        else:
            await interaction.response.send_message("I am not connected to a voice channel!", ephemeral=True)

    @app_commands.command(name="clear", description="Pause the player")
    async def clear(self, interaction: discord.Interaction):
        """Clears the queue"""
        player: Player = utils.get_guildplayer(interaction.guild)
        if not player == None:
            await player.clear()
            await interaction.response.send_message("Queue successfully cleared!")
            return
        await interaction.response.send_message("I am not connected to a voice channel!", ephemeral=True)

    # at this point; the user is in a VC and we're not
    # async with interaction.channel.typing():
    #     vc = await user_voice.channel.connect()
    #     await interaction.response.send_message("Joined your channel", ephemeral=True)
    #     player = await YTDLSource.from_url(url, loop=self.client.loop)
    # vc.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
    # while vc.is_playing():
    #     await asyncio.sleep(.1)

    # @app_commands.command(name="play", description="Play a song from YouTube")
    # async def play(self, interaction: discord.Interaction):
    #     player = guild_players[ctx.guild.id]
    #     if not await player.is_connected(ctx):
    #         return
    #     await player.pause(ctx)




            # await interaction.guild.change_voice_state(channel=interaction.guild.get_channel(interaction.user.voice.channel.id), self_deaf=True)
            # #await interaction.guild.voice_client.connect(self_deaf=True)#.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
            # async with interaction.channel.typing():
            # #try:
            #     voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            #     print(voice)
            #     player = await YTDLSource.from_url(query, loop=self.client.loop)
            #     voice.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

            # except:
            #     self.voiceClient.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

            # await self.embed.send_playing_status(self.client, ctx, 1, await self.queue.get_queue())
            # self.stopped = False
            # # self.player.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
            # while self.voiceClient.is_playing():
            #     await asyncio.sleep(.1)
            # if not self.voiceClient.is_paused() and not self.stopped:
            #     queue = await self.queue.get_queue()
            #     await self.queue.remove_from_queue(queue[0].id)
            #     if len(await self.queue.get_queue()) > 0:
            #         #self.player.play(discord.FFmpegPCMAudio(await self.queue.get_queue[0].url, **FFMPEG_OPTIONS))
            #         #await self.play((await self.queue.get_queue())[0].playUrl, ctx)
            #         await self.play((await self.queue.get_queue())[0].playUrl, ctx, (await self.queue.get_queue())[0].player)

            #await interaction.response.send_message("playing")

#     @commands.command(name='play', aliases=['p'])
#     async def play(self, ctx):

#         try:
#             # Get the current guild's player
#             player = guild_players[ctx.guild.id]
#         except KeyError:
#             # Create a player if it doesn't already exist
#             guild_players[ctx.guild.id] = Player(self.client)
#             player = guild_players[ctx.guild.id]

#         prefix = await self.client.get_prefix(ctx.message)

#         try:
#             voice_channel = ctx.author.voice.channel
#         except:
#             msg = await ctx.send(str(ctx.message.author.name) + " is not in a voice channel.", delete_after = 10.0)
#             return

#         # prepare the url
#         url = ctx.message.content.replace(prefix + "play", "")
#         if "www.youtube.com/watch?v=" in str(url):
#             if "&" in str(url):
#                 url = str(url).rpartition('&')[0].replace("watch?v=","")
#             else:
#                 url = str(url).replace("watch?v=","").replace("youtube.com", "youtu.be")

#         await player.addSong(url, ctx)

#     @commands.command()
#     async def pause(self, ctx):
#         player = guild_players[ctx.guild.id]
#         if not await player.is_connected(ctx):
#             return
#         await player.pause(ctx)

#     @commands.command()
#     async def resume(self, ctx):
#         player = guild_players[ctx.guild.id]
#         if not await player.is_connected(ctx):
#             return
#         await player.resume(ctx)

#     @commands.command()
#     async def stop(self, ctx):
#         player = guild_players[ctx.guild.id]
#         if not await player.is_connected(ctx):
#             return
#         await player.stop(ctx)

#     @commands.command()
#     async def skip(self, ctx):
#         player = guild_players[ctx.guild.id]
#         if not await player.is_connected(ctx):
#             return
#         await player.stop(ctx, False)
#         await player.queue.remove_from_queue((await player.queue.get_queue())[0].id)
#         await player.play((await player.queue.get_queue())[0].url, ctx, (await player.queue.get_queue())[0].player)

#     @commands.command()
#     async def skipTo(self, ctx, position):
#         player = guild_players[ctx.guild.id]
#         if not await player.is_connected(ctx):
#             return
#         for song in range(position):
#             try:
#                 await player.queue.remove_from_queue((await player.queue.get_queue())[0].id)
#             except:
#                 pass
#         await player.stop(ctx, False)
#         if len(await player.queue.get_queue()) > 0:
#             await player.play((await player.queue.get_queue())[0].url, ctx, (await player.queue.get_queue())[0].player)

#     @commands.command()
#     async def queue(self, ctx):
#         try:
#             player = guild_players[ctx.guild.id]
#         except KeyError:
#             embed = discord.Embed(title=f"\u200b", description="I am not connected to a voice channel", colour=0xff8700)
#             msg = await ctx.send(embed=embed, delete_after = 10.0)
#             return
            
#         queue = await player.queue.get_queue()
#         embed = discord.Embed(title=f"There are currently {len(queue)} track(s) in queue", description="Queue:", colour=0xff8700)
#         for index, i in enumerate(queue):
#             embed.add_field(name="\u200b", value=f"{index+1} [{i.title}]({i.url}) ({i.duration})", inline=False)
#         await ctx.send(embed=embed)

#     @commands.command()
#     async def disconnect(self, ctx):
#         vc = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
#         if vc == None:
#             return
#         vc.stop()
#        # await queue.clear_queue()
#         await ctx.message.add_reaction("\U0001F44B")
#         player = guild_players[ctx.guild.id]
#         await player.disconnect()
#         del guild_players[ctx.guild.id]
#         await vc.disconnect()

#     @commands.command()
#     async def dm_command(self, ctx, guild_id, channel_id, url):
#         if isinstance(ctx.channel, discord.channel.DMChannel):
#             if ctx.author.id == 581459918477852672:
                
#                 player = Player(self.client)
#                 await player.play_from_dm_command(guild_id, channel_id, url)

#             # channel = ctx.message.author.voice.channel

#             # voice = discord.utils.get(guild.voice_channels, id=channel_id)

#             # voice_client = discord.utils.get(self.client.voice_clients, guild=ctx.guild)

#             # if voice_client == None:
#             #     await voice.connect()
#             # else:
#             #     await voice_client.move_to(channel)


#         # if os.listdir("./AudioFiles") == []:
#         #     global queue
            

#         # # If there is it gets the filename from message.attachments
#         # if not str(ctx.message.attachments) == "[]":
#         #     print(ctx.message.attachments[0].url)
#         #     if ctx.message.attachments[0].url.endswith('mp3') or ctx.message.attachments[0].url.endswith('wav'):
#         #         split_v1 = str(ctx.message.attachments).split("filename='")[1]
#         #         filename = str(split_v1).split("' ")[0]
#         #         await embed.send_download_embed(ctx, filename)
#         #         await ctx.message.attachments[0].save(fp="./AudioFiles/{}".format(filename))
#         #         await queue.add_to_queue(filename)
#         #     else:
#         #         await ctx.message.channel.send("Invalid file type!")

#         #     await embed.send_download_success(filename)
# #######################
#         # # # queuList = await queue.get_queue()
#         # # # voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild) # This allows for more functionality with voice channels      
#         # # # if voice == None:
#         # # #     vc = await voice_channel.connect()

#         # # # FFMPEG_OPTIONS = {
#         # # # 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
#         # # # YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
#         # # # await queue.add_to_queue("dddd")
#         # # # if len(queuList) == 1:
#         # # #     with YoutubeDL(YDL_OPTIONS) as ydl:
#         # # #         info = ydl.extract_info(url, download=False)
#         # # #     URL = info['url']
#         # # #     vc = ctx.voice_client
#         # # #     vc.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
#         # # #     await embed.send_playing_status(3)
#         # # # else:
#         # # #     vc = ctx.voice_client
#         # # #     #await queue.add_to_queue(fname)
#         # # #     if vc.is_playing():
#         # # #         await embed.send_playing_status(3)
# #################################
#         # else:
#         #     t1 = threading.Thread(target=asyncio.get_event_loop().run_until_complete, args=(downloadFile(ctx.message.content,ctx,self.client, queue),))
#         #     try:
#         #         t1.start()
#         #     except ValueError as err:
#         #         await ctx.send(err.args)
#         #         return
      
# #     async def play_downloaded(self, client, ctx):
# #         global embed
# #         try:
# #             voice_channel = ctx.author.voice.channel
# #         except:
# #             await ctx.send(str(ctx.message.author.name) + " is not in a channel.")
# #             return
# #         if voice_channel != None:
# #             voice = discord.utils.get(client.voice_clients, guild=ctx.guild) # This allows for more functionality with voice channels      
# #             if voice == None:
# #                 vc = await voice_channel.connect()
# #             else:
# #                 vc = ctx.voice_client
# #             queueList = await queue.get_queue()
# #             track = queueList[0]
# #             # global embed
            
# #             await embed.send_playing_status(1)

# #             vc.play(discord.FFmpegPCMAudio(source=f"./AudioFiles/{track}")) #!Remove executable Path when dockerizing
# #             # Sleep while audio is playing.
# #             while vc.is_playing():
# #                 await asyncio.sleep(.1)
# #         else:
# #             await ctx.send(str(ctx.message.author.name) + "is not in a channel.")
# #         # Delete command after the audio is done playing.
# #         try:
# #             await ctx.message.delete()
# #         except:
# #             pass
# #         if not vc.is_paused():
# #             try:
# #                 await queue.remove_from_queue(track)
# #                 if await queue.get_queue() != []:
# #                     print(await queue.get_queue())
# #                     await Play.play_downloaded(self, self.client, ctx)
# #             except:
# #                 pass
#     @commands.Cog.listener()
#     async def on_voice_state_update(self, ctx, before, after):
#         vc = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
#         # Checking if the bot is connected to a channel and if there is only 1 member connected to it (the bot itself)
#         if vc is not None and len(vc.channel.members) == 1:
#             # You should also check if the song is still playing
#             await asyncio.sleep(200)
#             if vc is not None and len(vc.channel.members) == 1:
#                 player = guild_players[ctx.guild.id]
#                 await player.disconnect()
#                 guild_players[ctx.guild.id] = None
#         elif vc == None:
#             try:
#                 player = guild_players[ctx.guild.id]
#                 await player.disconnect()
#                 del guild_players[ctx.guild.id]
#             except:
#                 pass

#     # @commands.Cog.listener()
#     # async def on_disconnect(ctx):
#     #     del guild_players[ctx.guild.id]

async def setup(client):
    await client.add_cog(Play(client))
