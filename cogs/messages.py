import discord
from discord.ext import commands, tasks


import json

with open("config.json", "r") as read_file:
    config = json.load(read_file)


class Mesages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.GUILD = self.bot.get_guild(config["GUILD_ID"])
        self.GROUP_STUDY_CATEG = discord.utils.get(
            self.GUILD.categories, id=config["CATEGORY"]["GROUP"]
        )
        self.VIDEO_STUDY_CATEG = discord.utils.get(
            self.GUILD.categories, id=config["CATEGORY"]["VIDEO"]
        )
        self.SILENT_CATEG = discord.utils.get(
            self.GUILD.categories, id=config["CATEGORY"]["SILENT"]
        )
        self.EXTRACURRICULAR_CATEG = discord.utils.get(
            self.GUILD.categories, id=config["CATEGORY"]["EXTRACURRICULAR"]
        )
        self.LOUNGE_VC = discord.utils.get(
            self.GUILD.voice_channels, id=config["CHANNELS"]["VOICE"]["LOUNGE"]
        )
        self.COUNTER = discord.utils.get(
            self.GUILD.voice_channels, id=config["CHANNELS"]["VOICE"]["COUNTER"]
        )
        self.BOT_CHANNEL = discord.utils.get(
            self.GUILD.text_channels, id=config["CHANNELS"]["TEXT"]["KOMI_MESSAGES"]
        )
        self.TOMODACHI = self.GUILD.get_role(config["ROLES"]["TOMODACHI"])
        self.STUDYING = self.GUILD.get_role(config["ROLES"]["STUDYING"])
        self.kick_stalkers.start()

    ################# LOOPS #################

    @tasks.loop(minutes=config["KICK_STALKERS_AFTER"])
    async def kick_stalkers(self):
        # MOVE MEMBERS WHO DONT HAVE VIDEO OR SCREENSHARE
        for vc in self.VIDEO_STUDY_CATEG.voice_channels:
            for mem in vc.members:
                if not (mem.voice.self_video or mem.voice.self_stream):
                    await mem.move_to(channel=self.LOUNGE_VC)
                    await self.BOT_CHANNEL.send(
                        f"{mem.mention} was moved <:komi_sleep:843170281438576671>\n<#{vc.id}> -> <#{self.LOUNGE_VC.id}>\nReason : no camera or screenshare"
                    )
        # for vc in self.EXTRACURRICULAR_CATEG.voice_channels:
        #     for mem in vc.members:
        #         if not (mem.voice.self_video or mem.voice.self_stream):
        #             await mem.move_to(channel=self.LOUNGE_VC)
        #             await self.BOT_CHANNEL.send(
        #                 f"{mem.mention} was moved <:komi_sleep:843170281438576671>\n<#{vc.id}> -> <#{self.LOUNGE_VC.id}>\nReason : no camera or screenshare"
        #             )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or (before.channel == after.channel):
            return
        study_categ_ids = config["CATEGORY"].values()

        if after.channel != None:
            # WHEN SOMEONE JOINS A STUDY CHANNEL
            if after.channel.category_id in study_categ_ids:
                await member.add_roles(self.STUDYING)
                await member.remove_roles(self.TOMODACHI)
                perms = after.channel.category.overwrites_for(self.STUDYING)
                perms.view_channel = True
                perms.speak = False
                await after.channel.set_permissions(member, overwrite=perms)
                await member.edit(mute=True)
                msg = f"{member.mention} joined <#{after.channel.id}> <:komi_ok:843170247670366239>\n"
                if after.channel.category_id in (
                    self.VIDEO_STUDY_CATEG.id,
                    self.EXTRACURRICULAR_CATEG.id,
                ):
                    msg += f"**You need to share your screen or turn on camera or you will be moved to another channel**\n"
                msg += f"Head over to <#{config['CHANNELS']['TEXT']['ACCOUNTABILITY']}> and post some goals to get started\n"
                await self.BOT_CHANNEL.send(msg)
                if after.channel.category_id == config["CATEGORY"]["PRIVATE"]:
                    await member.edit(mute=False)
            else:
                await member.edit(mute=False)

        elif after.channel == None:
            # WHEN SOMEONE LEAVES A STUDY CHANNEL
            if before.channel.category_id in study_categ_ids:
                await member.add_roles(self.TOMODACHI)
                await member.remove_roles(self.STUDYING)
                await before.channel.set_permissions(member, overwrite=None)
                msg = f"**{member}** left <#{before.channel.id}> <:komi_sleep:843170281438576671> \n"
                await self.BOT_CHANNEL.send(msg)
            else:
                pass


def setup(bot):
    bot.add_cog(Mesages(bot))
    print("---> MESSAGES LOADED")
