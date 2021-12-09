import discord
from discord_components import (
    DiscordComponents,
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    Interaction,
    ActionRow,
)


class Embed():
    def __init__(self):
        self.message = None
        self.file = "" 
        self.skip_btn_id = "skip_btn"
        self.play_btn_id = "play_btn"
        self.pause_btn_id = "pause_btn"
        self.stop_btn_id = "stop_btn"

    # async def send_download_embed(self, ctx, file):
    #     embed = discord.Embed(title="Downloading file", description=str(file))
    #     self.message = await ctx.send(embed=embed)
    #     self.file = str(file)

    # async def send_download_success(self, file):
    #     embed = discord.Embed(title="Downloaded file", description=str(file))
    #     await self.message.edit(embed=embed)
    
    async def send_playing_status(self, client, ctx, status, queue, edit=False):
        """status:
        1: playing
        2: paused
        3: added to queue
        """

        async def callback(inter: Interaction):
            #await ctx.invoke(client.get_command('play'), query='hi')
            print(inter.custom_id)
            if inter.custom_id ==self.play_btn_id:
                await ctx.invoke(client.get_command('resume'))
            elif inter.custom_id ==self.pause_btn_id:
                await ctx.invoke(client.get_command('pause'))
            elif inter.custom_id ==self.skip_btn_id:
                await ctx.invoke(client.get_command('skip'))
            elif inter.custom_id ==self.stop_btn_id:
                await ctx.invoke(client.get_command('stop'))            
            
            await inter.respond(type=6)

        async def selectCallback(inter: Interaction):
            await inter.respond(type=6)
            await ctx.invoke(client.get_command('skipTo'), position=int(inter.values[0]))

        if status == 1:
            select_options = []
            for index, song in enumerate(queue):
                if index != 0:
                    select_options.append(SelectOption(label=song.title, value=index))
            if len(select_options) == 0:
                select_options = [SelectOption(label="No song in queue", value=-1),]

            # remove the queue selector from the last play embed to avoid errors
            if self.message != None:
                embed = discord.Embed(title="Playing", description=f"[{queue[0].title}]({queue[0].url}) ({queue[-1].duration})", colour=0xff8700)
                await self.message.edit(embed=embed, 
                    components=[
                        ActionRow(
                            client.components_manager.add_callback(
                                Button(emoji="⏭️", custom_id=self.skip_btn_id), callback
                            ),
                            client.components_manager.add_callback(
                                Button(emoji="⏸️", custom_id=self.pause_btn_id), callback
                            ),
                            client.components_manager.add_callback(
                                Button(emoji="▶️", custom_id=self.play_btn_id), callback
                            ),
                            client.components_manager.add_callback(
                                Button(emoji="⏹️", custom_id=self.stop_btn_id), callback
                            ),
                        ),
                        ActionRow(
                            client.components_manager.add_callback(
                                Select(
                                    placeholder="Session expired",
                                    options=select_options,
                                    custom_id="select1",
                                    disabled=True,
                                ), selectCallback
                            ),
                        )
                    ],
                )

            embed = discord.Embed(title="Playing", description=f"[{queue[0].title}]({queue[0].url}) ({queue[-1].duration})", colour=0xff8700)
            self.message = await ctx.send(embed=embed, 
                components=[
                    ActionRow(
                        client.components_manager.add_callback(
                            Button(emoji="⏭️", custom_id=self.skip_btn_id), callback
                        ),
                        client.components_manager.add_callback(
                            Button(emoji="⏸️", custom_id=self.pause_btn_id), callback
                        ),
                        client.components_manager.add_callback(
                            Button(emoji="▶️", custom_id=self.play_btn_id), callback
                        ),
                        client.components_manager.add_callback(
                            Button(emoji="⏹️", custom_id=self.stop_btn_id), callback
                        ),
                    ),
                    ActionRow(
                        client.components_manager.add_callback(
                            Select(
                                placeholder="Skip to",
                                options=select_options,
                                custom_id="select1",
                                disabled=True if select_options[0].value == -1 else False,
                            ), selectCallback
                        ),
                    )
                ],
            )
            return
        elif status == 2:
            embed = discord.Embed(title="Paused", description=f"[{queue[0].title}]({queue[0].url}) ({queue[-1].duration})", colour=0xff8700)
        elif status == 3:
            embed = discord.Embed(title="Queued", description=f"[{queue[-1].title}]({queue[-1].url}) ({queue[-1].duration})", colour=0xff8700)
            await ctx.send(embed=embed)
            select_options = []
            for index, song in enumerate(queue):
                if index != 0:
                    select_options.append(SelectOption(label=song.title, value=index))
            if len(select_options) == 0:
                select_options = [SelectOption(label="No song in queue", value=-1),]
            embed = discord.Embed(title="Playing", description=f"[{queue[0].title}]({queue[0].url}) ({queue[-1].duration})", colour=0xff8700)
            await self.message.edit(embed=embed, 
                components=[
                    ActionRow(
                        client.components_manager.add_callback(
                            Button(emoji="⏭️", custom_id=self.skip_btn_id), callback
                        ),
                        client.components_manager.add_callback(
                            Button(emoji="⏸️", custom_id=self.pause_btn_id), callback
                        ),
                        client.components_manager.add_callback(
                            Button(emoji="▶️", custom_id=self.play_btn_id), callback
                        ),
                        client.components_manager.add_callback(
                            Button(emoji="⏹️", custom_id=self.stop_btn_id), callback
                        ),
                    ),
                    ActionRow(
                        client.components_manager.add_callback(
                            Select(
                                placeholder="No songs in queue" if select_options[0].value == -1 else "Skip to",
                                options=select_options,
                                custom_id="select1",
                                disabled=True if select_options[0].value == -1 else False,
                            ), selectCallback
                        ),
                    )
                ],
            )
        # if self.message == None:
        #     await ctx.send(embed=embed)
        # else:
        #     await self.message.edit(embed=embed)

    async def delete_embed(self):
        await self.message.delete()

    async def disconnect(self):
        if self.message != None:
                embed = discord.Embed(title="Playing", colour=0xff8700)
                await self.message.edit(embed=embed, 
                    components=[
                        ActionRow(
                            Button(emoji="⏭️", custom_id=self.skip_btn_id),
                            Button(emoji="⏸️", custom_id=self.pause_btn_id),
                            Button(emoji="▶️", custom_id=self.play_btn_id),
                            Button(emoji="⏹️", custom_id=self.stop_btn_id),
                        ActionRow(
                                Select(
                                    placeholder="Session expired",
                                    options=SelectOption("x"),
                                    custom_id="select1",
                                    disabled=True,
                                ),
                            ),
                        )
                    ],
                )