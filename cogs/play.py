import discord
from discord.ext import commands
# from pyvirtualdisplay import Display
# from selenium import webdriver
# import time
# import os
# import asyncio
# import threading
import asyncio
from player import Player

# async def downloadFile(url, ctx, client, queue):
    #     url = url.replace(prefix + "play", "").strip()
    #     display = Display(visible=0, size=(800, 600))
    #     display.start()
    #     chrome_options = webdriver.ChromeOptions()
    #     chrome_options.add_argument('--no-sandbox')
    #     chrome_options.add_experimental_option('prefs', {
    #     'download.default_directory': f"{os.getcwd()}/AudioFiles",
    #     'download.prompt_for_download': False,
    #     })
    #     driver = webdriver.Chrome(chrome_options=chrome_options)

    #     driver.get(url)
    #     driver.find_element_by_xpath("//button[@class='button welcome__button welcome__button--accept button--enabled']").click()
    #     time.sleep(3)
    #     driver.implicitly_wait(5)

    #     #Select download file
    #     driver.find_element_by_xpath("//button[@class='transfer__button']").click()
    #     time.sleep(2)
    #     if driver.find_element_by_xpath("//h6[@class='file-system-entry__title']").text[-3:] == "wav" or driver.find_element_by_xpath("//h6[@class='file-system-entry__title']").text[-3:] == "mp3":
    #         global embed
    #         try:
    #             await embed.delete_embed()
    #         except:
    #             pass
    #         embed = Embed()
    #         title = driver.find_element_by_xpath("//h6[@class='file-system-entry__title']").text
    #         await embed.send_download_embed(ctx, str(title))

    #         driver.find_element_by_xpath("//button[@class='transfer__button']").click()
    #         wait = True
    #         while wait:
    #             for fname in os.listdir("./AudioFiles"):
    #                 if not fname.endswith('.crdownload'):
    #                     driver.quit()
    #                     display.stop()
    #                     wait = False
    #                     await queue.add_to_queue(fname)
    #                     await embed.send_download_success(fname)

    #                 queuList = await queue.get_queue()
    #                 if len(queuList) == 1:
    #                     print("oiegoseg")
    #                     await Play.play_downloaded(Play, client, ctx)

    #     else:
    #         raise ValueError('Invalid File type')
        
guild_players = {}

class Play(commands.Cog):

    def __init__(self, client):
        self.client = client
        #self.player = None


    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx):

        # if discord.utils.get(self.client.voice_clients, guild=ctx.guild) == None:
        #     try:
        #         del guild_players[ctx.guild.id]
        #     except:
        #         pass
                
        try:
            # Get the current guild's player
            player = guild_players[ctx.guild.id]
        except KeyError:
            # Create a player if it doesn't already exist
            guild_players[ctx.guild.id] = Player(self.client)
            player = guild_players[ctx.guild.id]


        # if self.player == None:
        #     self.player = Player(self.client)

        prefix = await self.client.get_prefix(ctx.message)

        url = ctx.message.content.replace(prefix + "play", "")
        try:
            voice_channel = ctx.author.voice.channel
        except:
            await ctx.send(str(ctx.message.author.name) + " is not in a channel.")
            return

        
        if "www.youtube.com/watch?v=" in str(url):
            if "&" in str(url):
                url = str(url).rpartition('&')[0].replace("watch?v=","")
            else:
                url = str(url).replace("watch?v=","")


        if not await player.is_connected(ctx):
            await player.connect(ctx, voice_channel)
            songTitle, songUrl, playUrl, duration = await player.get_Title(url)
            await player.queue.add_to_queue(songTitle, songUrl, playUrl, duration)
            await player.play(url,ctx)

        elif len(await player.queue.get_queue()) == 0:
            Title, Url, playUrl, duration = await player.get_Title(url)
            await player.queue.add_to_queue(Title, Url, playUrl, duration)
            await player.play(playUrl, ctx)
        else:
            Title, Url, playUrl, duration = await player.get_Title(url)
            await player.queue.add_to_queue(Title, Url, playUrl, duration)
            await player.embed.send_playing_status(ctx, 3, await player.queue.get_queue())

    @commands.command()
    async def pause(self, ctx):
        player = guild_players[ctx.guild.id]
        if not await player.is_connected(ctx):
            return
        await player.pause(ctx)

    @commands.command()
    async def resume(self, ctx):
        player = guild_players[ctx.guild.id]
        if not await player.is_connected(ctx):
            return
        await player.resume(ctx)

    @commands.command()
    async def stop(self, ctx):
        player = guild_players[ctx.guild.id]
        if not await player.is_connected(ctx):
            return
        await player.stop(ctx)

    @commands.command()
    async def skip(self, ctx):
        player = guild_players[ctx.guild.id]
        if not await player.is_connected(ctx):
            return
        await player.stop(ctx)
        #await self.player.play((await self.player.queue.get_queue())[0].url, ctx)

    @commands.command()
    async def queue(self, ctx):
        try:
            player = guild_players[ctx.guild.id]
        except KeyError:
            embed = discord.Embed(title=f"\u200b", description="I am not connected to a voice channel", colour=0xff8700)
            await ctx.send(embed=embed)
            return
            
        queue = await player.queue.get_queue()
        embed = discord.Embed(title=f"There are currently {len(queue)} track(s) in queue", description="Queue:", colour=0xff8700)
        for index, i in enumerate(queue):
            embed.add_field(name="\u200b", value=f"{index+1} [{i.title}]({i.url}) ({i.duration})", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def disconnect(self, ctx):
        vc = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if vc == None:
            return
        vc.stop()
       # await queue.clear_queue()
        await ctx.message.add_reaction("\U0001F44B")
        del guild_players[ctx.guild.id]
        await vc.disconnect()


        # if os.listdir("./AudioFiles") == []:
        #     global queue
            

        # # If there is it gets the filename from message.attachments
        # if not str(ctx.message.attachments) == "[]":
        #     print(ctx.message.attachments[0].url)
        #     if ctx.message.attachments[0].url.endswith('mp3') or ctx.message.attachments[0].url.endswith('wav'):
        #         split_v1 = str(ctx.message.attachments).split("filename='")[1]
        #         filename = str(split_v1).split("' ")[0]
        #         await embed.send_download_embed(ctx, filename)
        #         await ctx.message.attachments[0].save(fp="./AudioFiles/{}".format(filename))
        #         await queue.add_to_queue(filename)
        #     else:
        #         await ctx.message.channel.send("Invalid file type!")

        #     await embed.send_download_success(filename)
#######################
        # # # queuList = await queue.get_queue()
        # # # voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild) # This allows for more functionality with voice channels      
        # # # if voice == None:
        # # #     vc = await voice_channel.connect()

        # # # FFMPEG_OPTIONS = {
        # # # 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        # # # YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        # # # await queue.add_to_queue("dddd")
        # # # if len(queuList) == 1:
        # # #     with YoutubeDL(YDL_OPTIONS) as ydl:
        # # #         info = ydl.extract_info(url, download=False)
        # # #     URL = info['url']
        # # #     vc = ctx.voice_client
        # # #     vc.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        # # #     await embed.send_playing_status(3)
        # # # else:
        # # #     vc = ctx.voice_client
        # # #     #await queue.add_to_queue(fname)
        # # #     if vc.is_playing():
        # # #         await embed.send_playing_status(3)
#################################
        # else:
        #     t1 = threading.Thread(target=asyncio.get_event_loop().run_until_complete, args=(downloadFile(ctx.message.content,ctx,self.client, queue),))
        #     try:
        #         t1.start()
        #     except ValueError as err:
        #         await ctx.send(err.args)
        #         return
      
#     async def play_downloaded(self, client, ctx):
#         global embed
#         try:
#             voice_channel = ctx.author.voice.channel
#         except:
#             await ctx.send(str(ctx.message.author.name) + " is not in a channel.")
#             return
#         if voice_channel != None:
#             voice = discord.utils.get(client.voice_clients, guild=ctx.guild) # This allows for more functionality with voice channels      
#             if voice == None:
#                 vc = await voice_channel.connect()
#             else:
#                 vc = ctx.voice_client
#             queueList = await queue.get_queue()
#             track = queueList[0]
#             # global embed
            
#             await embed.send_playing_status(1)

#             vc.play(discord.FFmpegPCMAudio(source=f"./AudioFiles/{track}")) #!Remove executable Path when dockerizing
#             # Sleep while audio is playing.
#             while vc.is_playing():
#                 await asyncio.sleep(.1)
#         else:
#             await ctx.send(str(ctx.message.author.name) + "is not in a channel.")
#         # Delete command after the audio is done playing.
#         try:
#             await ctx.message.delete()
#         except:
#             pass
#         if not vc.is_paused():
#             try:
#                 await queue.remove_from_queue(track)
#                 if await queue.get_queue() != []:
#                     print(await queue.get_queue())
#                     await Play.play_downloaded(self, self.client, ctx)
#             except:
#                 pass
    @commands.Cog.listener()
    async def on_voice_state_update(self, ctx, before, after):
        vc = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        # Checking if the bot is connected to a channel and if there is only 1 member connected to it (the bot itself)
        if vc is not None and len(vc.channel.members) == 1:
            # You should also check if the song is still playing
            await asyncio.sleep(600)
            if vc is not None and len(vc.channel.members) == 1:
                guild_players[ctx.guild.id] = None
                await vc.disconnect()
        elif vc == None:
            try:
                del guild_players[ctx.guild.id]
            except:
                pass

    # @commands.Cog.listener()
    # async def on_disconnect(ctx):
    #     del guild_players[ctx.guild.id]

def setup(client):
    client.add_cog(Play(client))
