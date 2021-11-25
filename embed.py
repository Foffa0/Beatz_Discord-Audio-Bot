import discord


class Embed():
    def __init__(self):
        self.message = None
        self.file = "" 

    # async def send_download_embed(self, ctx, file):
    #     embed = discord.Embed(title="Downloading file", description=str(file))
    #     self.message = await ctx.send(embed=embed)
    #     self.file = str(file)

    # async def send_download_success(self, file):
    #     embed = discord.Embed(title="Downloaded file", description=str(file))
    #     await self.message.edit(embed=embed)

   
    async def send_playing_status(self, ctx, status, queue):
        """status:
        1: playing
        2: paused
        3: added to queue
        """
        if status == 1:
            embed = discord.Embed(title="Playing", description=f"[{queue[0].title}]({queue[0].url})", colour=0xff8700)
            self.message = await ctx.send(embed=embed)
            return
        elif status == 2:
            embed = discord.Embed(title="Paused", description=f"[{queue[0].title}]({queue[0].url})", colour=0xff8700)
        elif status == 3:
            embed = discord.Embed(title="Queued", description=f"[{queue[-1].title}]({queue[-1].url})", colour=0xff8700)
            await ctx.send(embed=embed)
            return
        if self.message == None:
            await ctx.send(embed=embed)
        else:
            await self.message.edit(embed=embed)

    async def delete_embed(self):
        await self.message.delete()