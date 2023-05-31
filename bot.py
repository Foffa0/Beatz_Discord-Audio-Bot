import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.all()
intents.message_content = True


discord.utils.setup_logging()

# token = os.environ.get('BOT_TOKEN')

# default_prefix = '.'

# async def determine_prefix(bot,message):
#     guild = message.guild
#     settings = Settings()
#     #Only allow custom prefixs in guild
#     if guild:
#         return await settings.getPrefix(guild.id)
#         #return custom_prefixes.get(guild.id, default_prefixes)
#     else:
#         return default_prefix

#client = commands.Bot(command_prefix = determine_prefix)
#client = commands.Bot(command_prefix='!')

client = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description='Relatively simple music bot example',
    intents=intents,
)
#tree = discord.app_commands.CommandTree(client)

async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await client.load_extension(f'cogs.{filename[:-3]}')



@client.event
async def on_ready():
    await client.tree.sync()
    print(f'We have logged in as {client.user}')


async def main():
    await load()
    await client.start()     

#client.run('')
asyncio.run(main())