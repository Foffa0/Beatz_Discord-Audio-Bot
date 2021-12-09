from discord import client
from discord.ext import commands

from Settings import Settings

class Prefix(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.guild_only()
    async def setprefix(self, ctx, *, prefixes=""):
        if len(prefixes) > 5:
            await ctx.send("Prefix too long! (maximum 5 characters)")
            return
        elif " " in prefixes:
            await ctx.send("No whitespace in prefix allowed!")
            return
        #You'd obviously need to do some error checking here
        #All I'm doing here is if prefixes is not passed then
        #set it to default 
        #custom_prefixes[ctx.guild.id] = prefixes or default_prefixes
        settings = Settings()
        await settings.set_Prefix(ctx.guild.id, prefixes)

        await ctx.send(f"Prefix set to {prefixes}")

def setup(client):
    client.add_cog(Prefix(client))