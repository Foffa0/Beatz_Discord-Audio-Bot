import discord
from discord import app_commands
from discord.ext import commands
from player import Player
import utils

class General(commands.Cog):
    """ A collection of the commands for moving the bot around in you server and change settings.
    """

    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("General cog loaded.")

    @app_commands.command(name="connect", description="Connect the bot to your voice channel")
    async def connect(self, interaction: discord.Interaction):
        user_voice = interaction.user.voice
        if not user_voice:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True, delete_after=30)
            return
        else:
            bot_voice = interaction.guild.voice_client

        if bot_voice:
            # we're in a channel already
            if bot_voice.channel.id == user_voice.channel.id:
                # in the same voice channel as the user already
                await interaction.response.send_message("Bot is already in your VC", ephemeral=True, delete_after=30)
                return

            # move channels now - we're in VC but not the user's VC
            await bot_voice.move_to(user_voice.channel)
            await interaction.response.send_message("Moved to your channel", delete_after=30)
            return

        # at this point; the user is in a VC and we're not
        utils.guild_players[interaction.guild] = Player(self.client, interaction.guild)
        player = utils.guild_players[interaction.guild]
        await player.connect_voice_channel(user_voice.channel)
        await interaction.response.send_message("Connected to your channel", delete_after=30)

    @app_commands.command(name="disconnect", description="Disonnect the bot from your voice channel")
    async def disconnect(self, interaction: discord.Interaction):
        user_voice = interaction.user.voice
        if not user_voice:
            await interaction.response.send_message("You are not in a voice channel!", delete_after=30)
            return
        else:
            bot_voice = interaction.guild.voice_client
        
        if bot_voice:
            # we're in a channel already
            if bot_voice.channel.id == user_voice.channel.id:
                # in the same voice channel as the user already
                player = utils.guild_players[interaction.guild]
                await player.disconnect_voice_channel(interaction.guild.voice_client)
                await interaction.response.send_message("Bye :wave:", delete_after=30)
                return
        await interaction.response.send_message("I am not connected to a voice channel", delete_after=30)
        

async def setup(client):
    await client.add_cog(General(client))
