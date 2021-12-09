import discord
from discord import message
from discord.ext import commands
import os
from Settings import Settings
from discord_components import DiscordComponents


token = os.environ.get('BOT_TOKEN')

default_prefix = '.'

async def determine_prefix(bot,message):
    guild = message.guild
    settings = Settings()
    #Only allow custom prefixs in guild
    if guild:
        return await settings.getPrefix(guild.id)
        #return custom_prefixes.get(guild.id, default_prefixes)
    else:
        return default_prefix

client = commands.Bot(command_prefix = determine_prefix)
#client = commands.Bot(command_prefix='!')



for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

@client.event
async def on_ready():
    DiscordComponents(client)
    print('Logged in as {}'.format(client.user.name))
    # for file in os.listdir("./AudioFiles"):
    #     os.remove(f"./AudioFiles/{file}")
           
# TODO remove token
client.run("ODYzNDg3MjkyNTAwODY5MTQw.YOnnNQ.NqhF7IbL-7zhoI2tBklMeChMbDs")