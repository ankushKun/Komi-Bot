import discord
from discord.ext import commands
import json

with open("config.json", "r") as read_file:
    config = json.load(read_file)

SERVERS = config["INTEGRATIONS"]


class OSI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or (before.channel == after.channel):
            return
        study_categ_ids = config["CATEGORY"].values()

        if after.channel != None and after.channel.category_id in study_categ_ids:
            # WHEN SOMEONE JOINS A STUDY CHANNEL
            for guild_id in SERVERS:
                guild = self.bot.get_guild(int(guild_id))
                if member.id in [mem.id for mem in guild.members]:
                    role1 = guild.get_role(SERVERS[guild_id][0])  # STUDYING ROLE
                    role2 = guild.get_role(SERVERS[guild_id][1])  # NORMAL ROLE
                    m = guild.get_member(member.id)
                    await m.add_roles(role1)
                    await m.remove_roles(role2)

        elif after.channel == None and before.channel.category_id in study_categ_ids:
            # WHEN SOMEONE JOINS A STUDY CHANNEL
            # REMOVE ROLE ON OTHER SERVER
            for guild_id in SERVERS:
                guild = self.bot.get_guild(int(guild_id))
                if member.id in [mem.id for mem in guild.members]:
                    role1 = guild.get_role(SERVERS[guild_id][0])  # STUDYING ROLE
                    role2 = guild.get_role(SERVERS[guild_id][1])  # NORMAL ROLE
                    m = guild.get_member(member.id)
                    await m.remove_roles(role1)
                    await m.add_roles(role2)


def setup(bot):
    bot.add_cog(OSI(bot))
    print("---> OSI LOADED")
