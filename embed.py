from typing import Optional
import discord
from song import Song
from discord.ext import commands
from config import config

STOPPED_MSG = "Currently not playing"
PAUSED_MSG = "Paused"
PLAYING_MSG = "Currently playing"

PREV_ID = "1"
PAUSE_ID = "2"
RESUME_ID = "3"
NEXT_ID = "4"

class PlayerView(discord.ui.View):

    def __init__(self, player):
        super().__init__()
        self.player = player

    @discord.ui.button(emoji=discord.PartialEmoji.from_str('◀️'), custom_id=PREV_ID)
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.previous()
        embed, url_view = self.player.playerEmbed.build_embed()
        await interaction.response.edit_message(embed=embed, view=url_view)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str('⏯️'), custom_id=PAUSE_ID)
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.player.is_paused():
            await self.player.resume()
        elif self.player.is_playing():
            await self.player.pause()

        embed, url_view = self.player.playerEmbed.build_embed()
        await interaction.response.edit_message(embed=embed, view=url_view)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str('⏭️'), custom_id=NEXT_ID)
    async def grey(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.skip()
        embed, url_view = self.player.playerEmbed.build_embed()
        await interaction.response.edit_message(embed=embed, view=url_view)


class PlayerEmbed():

    def __init__(self, player, client):
        """Player states: 1=playing, 2=paused, 3=stopped"""
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

        embed.set_author(name=title)
        if self.player.current_song == None:
            embed.title = "No song selected"
        else:
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

