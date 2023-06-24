from typing import List, Optional
import discord
from discord.components import SelectOption
from discord.utils import MISSING
from song import Song
from discord.ext import commands
from config import config
import datetime

STOPPED_MSG = "Currently not playing"
PAUSED_MSG = "is paused"
PLAYING_MSG = "is currently playing"

PREV_ID = "1"
PAUSE_ID = "2"
RESUME_ID = "3"
NEXT_ID = "4"
SELECT_ID = "5"

class PlayerView(discord.ui.View):

    def __init__(self, player):
        super().__init__()
        self.player = player

    @discord.ui.button(emoji=discord.PartialEmoji.from_str('◀️'), custom_id=PREV_ID)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.previous()
        embed = self.player.playerEmbed.generalEmbed(title="Changing Song")
        await interaction.response.edit_message(embed=embed)
        embed, view = self.player.queueEmbed.build()
        await self.player.queueEmbed.msg.edit(embed=embed, view=view)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str('⏯️'), custom_id=PAUSE_ID)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.player.is_paused():
            await self.player.resume()
        elif self.player.is_playing():
            await self.player.pause()

        embed, url_view = self.player.playerEmbed.build_embed()
        await interaction.response.edit_message(embed=embed, view=url_view)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str('⏭️'), custom_id=NEXT_ID)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.skip()
        embed, url_view = self.player.playerEmbed.build_embed()
        await interaction.response.edit_message(embed=embed, view=url_view)
        embed, view = self.player.queueEmbed.build()
        await self.player.queueEmbed.msg.edit(embed=embed, view=view)


class CustomSelect(discord.ui.Select):

    def __init__(self, options, player):
        super().__init__(custom_id=SELECT_ID, placeholder="Skip to song", options=options)
        self.player = player

    async def callback(self, interaction: discord.Interaction):
        await self.player.skip(int(self.values[0]))
        embed, view = self.player.queueEmbed.build()
        await interaction.response.edit_message(embed=embed, view=view)


class PlayerEmbed():

    def __init__(self, player, client):
        self.player = player
        self.client: commands.Bot = client
        self.msg = None

    def build_embed(self):
        if self.player.is_playing():
            title = PLAYING_MSG
        elif self.player.is_paused():
            title = PAUSED_MSG
        else:
            title = STOPPED_MSG 

        embed = discord.Embed(color=config.EMBED_COLOR)

        embed.description = title

        if self.player.current_song == None:
            embed.title = "No song selected"
        else:
            embed.set_author(name=self.player.current_song.channel, icon_url=self.player.current_song.channel_thumbnail)

            embed.title = self.player.current_song.title
            embed.url = self.player.current_song.url
            embed.set_image(url=self.player.current_song.thumbnail)
        url_view = PlayerView(self.player)

        return embed, url_view
    
    def generalEmbed(self, title, content=None):
        embed = discord.Embed(title=title, color=config.EMBED_COLOR)
        embed.title = title
        embed.description = content
        return embed

class QueueEmbed():

    def __init__(self, player, client):
        self.player = player
        self.client: commands.Bot = client
        self.msg = None

    def build(self):
        embed = discord.Embed(color=config.EMBED_COLOR)

        if len(self.player.playlist.playque) == 0:
            embed.title = "There are currently no songs in queue"
            embed.description = "Add one with `/play`"
            return embed

        embed.title = "Song queue"
        options = []
        for id, song in enumerate(self.player.playlist.playque):
            if id == 0:
                embed.add_field(name="**Currently playing:**", value=song.title + " (" + str(datetime.timedelta(seconds=song.duration)) + ")")
                continue
            embed.add_field(name="", value=f'**{id}.**    ' + song.title + " (" + str(datetime.timedelta(seconds=song.duration)) + ")", inline=False)
            options.append(discord.SelectOption(label=id, description=song.title, value=id))

        view = None
        if len(options) > 0:
            view = discord.ui.View()
            view.add_item(CustomSelect(options, self.player))

        return embed, view
