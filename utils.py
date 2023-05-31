import asyncio

# A dictionary that saves which player belongs to which guild
guild_players = {}


def get_guildplayer(guild):

    try:
        player = guild_players[guild]
    except:
        player = None
    return player

def setGuildPlayer(guild, player):
    guild_players[guild] = player

# class Timer:
#     def __init__(self, callback):
#         self._callback = callback
#         self._task = asyncio.create_task(self._job())

#     async def _job(self):
#         await asyncio.sleep(config.VC_TIMEOUT)
#         await self._callback()

#     def cancel(self):
#         self._task.cancel()