import json

class Settings():

    async def register_new_guild(guildId):
        with open("./data_files/settings.json", "r") as read_file:
            data = json.load(read_file)
            for guild in data["guilds"]:
                if guildId == guild["id"]:
                    return
            guildSettings = {
                "id": guildId,
                "prefix": "."
            }
            data["guilds"].append(guildSettings)
            with open("./data_files/settings.json", "w") as write_file:
                json.dump(data, write_file)

    async def getSettings():
        with open("./data_files/settings.json", "r") as read_file:
            data = json.load(read_file)
        
    async def getPrefix(self, guildId):
        with open("./data_files/settings.json", "r") as read_file:
            data = json.load(read_file)
            for guild in data["guilds"]:
                if guildId == guild["id"]:
                    return guild["prefix"]
            await Settings.register_new_guild(guildId)

            with open("./data_files/settings.json", "r") as read_file:
                data = json.load(read_file)
                for guild in data["guilds"]:
                    if guildId == guild["id"]:
                        return guild["prefix"]
    
    async def set_Prefix(self, guildId, prefix):
        with open("./data_files/settings.json", "r") as read_file:
            data = json.load(read_file)
            for i, guild in enumerate(data["guilds"]):
                if guildId == guild["id"]:
                    data["guilds"][i]["prefix"] = str(prefix)
        with open("./data_files/settings.json", "w") as write_file:
            json.dump(data, write_file)
