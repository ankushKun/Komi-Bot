import discord
from discord.ext import commands, tasks
import json
from decouple import config as env
from datetime import datetime
from pytz import timezone

with open("config.json", "r") as read_file:
    config = json.load(read_file)

SERVERS = config["INTEGRATIONS"]

import pyrebase

if config["USE_FIREBASE_JSON"] == 1:  # 0 to use env, 1 to use json
    with open("firebase.json", "r") as read_file:
        firebase = pyrebase.initialize_app(json.load(read_file))
else:
    firebase = pyrebase.initialize_app(json.loads(env("FIREBASE_CONFIG")))
db = firebase.database()


class OSI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.KOMI = self.bot.get_guild(config["GUILD_ID"])
        self.BOT_CHN = self.KOMI.get_channel(
            config["CHANNELS"]["TEXT"]["KOMI_MESSAGES"]
        )
        self.studying = []
        self.OSI_add_mins.start()
        self.OSI_reset.start()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        common_servers = member.mutual_guilds
        if (
            member.bot
            or (before.channel == after.channel)
            or not config["GUILD_ID"] in [s.id for s in common_servers]
        ):
            return
        study_categ_ids = config["CATEGORY"].values()

        async def give_studying():
            for server in common_servers:
                if str(server.id) in SERVERS:
                    role1 = server.get_role(
                        SERVERS[str(server.id)]["STUDYING"]
                    )  # STUDYING ROLE
                    role2 = server.get_role(
                        SERVERS[str(server.id)]["NORMAL"]
                    )  # NORMAL ROLE
                    m = server.get_member(member.id)
                    try:
                        await m.remove_roles(role2)
                        await m.add_roles(role1)
                    except:
                        pass

        async def remove_studying():
            for server in common_servers:
                if str(server.id) in SERVERS:
                    role1 = server.get_role(
                        SERVERS[str(server.id)]["STUDYING"]
                    )  # STUDYING ROLE
                    role2 = server.get_role(
                        SERVERS[str(server.id)]["NORMAL"]
                    )  # NORMAL ROLE
                    m = server.get_member(member.id)
                    try:
                        await m.remove_roles(role1)
                        await m.add_roles(role2)
                    except:
                        pass

        ### VC IN KOMI SAN
        if after.channel != None and after.channel.category_id in study_categ_ids:
            # WHEN SOMEONE JOINS A STUDY CHANNEL
            give_studying()

        elif after.channel == None and before.channel.category_id in study_categ_ids:
            # WHEN SOMEONE LEAVES A STUDY CHANNEL
            # REMOVE ROLE ON OTHER SERVER
            remove_studying()

        # WHEN JOINED A STUDY VC ON ANOTHER SERVER
        if after.channel != None and str(after.channel.guild.id) in SERVERS:
            if (
                after.channel.category.id
                == SERVERS[str(after.channel.guild.id)]["CATEGORY"]
            ):
                await self.BOT_CHN.send(
                    f"**{member}** joined `{after.channel}` in **{after.channel.guild}**"
                )
                self.studying.append((member.id, after.channel.guild.id))
                give_studying()

        # WHEN LEFT A STUDY VC ON ANOTHER SERVER
        elif (
            before.channel != None
            and str(before.channel.guild.id) in SERVERS
            and after.channel == None
        ):
            if (
                before.channel.category.id
                == SERVERS[str(before.channel.guild.id)]["CATEGORY"]
            ):
                await self.BOT_CHN.send(
                    f"**{member}** left `{before.channel}` in **{before.channel.guild}**"
                )
                self.studying.remove((member.id, before.channel.guild.id))
                remove_studying()

    @tasks.loop(minutes=config["TIMER_INTERVAL"])
    async def OSI_add_mins(self):
        mins_to_add = config["TIMER_INTERVAL"]

        for data in self.studying:
            user_id = data[0]
            server_id = data[1]
            t = (
                db.child("TIMINGS")
                .child(user_id)
                .child("OSI")
                .child(server_id)
                .get()
                .val()
            )

            if t == None:
                db.child("TIMINGS").child(user_id).child("OSI").child(server_id).set(
                    {
                        "TOTAL": mins_to_add,
                        "P24H": mins_to_add,
                        "P7D": mins_to_add,
                        "P1M": mins_to_add,
                    }
                )
            else:
                for key in t:
                    t[key] = t[key] + mins_to_add
                db.child("TIMINGS").child(user_id).child("OSI").child(server_id).set(t)

        await self.BOT_CHN.send(
            f"> `[OSI]` updated timings [`{datetime.now(timezone('GMT'))} GMT`]"
        )

    @tasks.loop(minutes=30)
    async def OSI_reset(self):
        now = datetime.now(timezone("GMT"))
        if now.hour == 0:
            times = dict(db.child("TIMINGS").get().val())
            for id_ in times:  # USER IDS
                try:
                    for server_ in times[id_]["OSI"]:  # SERVER IDS IN USERS ID OSI
                        times[id_]["OSI"][server_]["P24H"] = 0
                except:
                    continue
            db.child("TIMINGS").set(times)
            await self.BOT_CHN.send(
                f"> `[OSI]` reset last 24 hours timer at `{datetime.now(timezone('GMT'))} GMT`"
            )
            if now.weekday() == 0:
                times = dict(db.child("TIMINGS").get().val())
                for id_ in times:  # USER IDS
                    try:
                        for server_ in times[id_]["OSI"]:  # SERVER IDS IN USERS ID OSI
                            times[id_]["OSI"][server_]["P7D"] = 0
                    except:
                        continue
                db.child("TIMINGS").set(times)
                await self.BOT_CHN.send(
                    f"> `[OSI]` reset last 7 days timer at `{datetime.now(timezone('GMT'))} GMT`"
                )
            if now.day == 1:
                times = dict(db.child("TIMINGS").get().val())
                for id_ in times:  # USER IDS
                    try:
                        for server_ in times[id_]["OSI"]:  # SERVER IDS IN USERS ID OSI
                            times[id_]["OSI"][server_]["P1M"] = 0
                    except:
                        continue
                db.child("TIMINGS").set(times)
                await self.BOT_CHN.send(
                    f"> `[OSI]` reset last 1 months timer at `{datetime.now(timezone('GMT'))} GMT`"
                )

    @commands.command()
    @commands.is_owner()
    async def OSI_manualreset(self, ctx, which):
        if which == "day":
            times = dict(db.child("TIMINGS").get().val())
            for id_ in times:  # USER IDS
                try:
                    for server_ in times[id_]["OSI"]:  # SERVER IDS IN USERS ID OSI
                        times[id_]["OSI"][server_]["P24H"] = 0
                except:
                    continue
            db.child("TIMINGS").set(times)
            await self.BOT_CHN.send(
                f"> `[OSI]` manual reset last 24 hours timer at `{datetime.now(timezone('GMT'))} GMT`"
            )
        elif which == "week":
            times = dict(db.child("TIMINGS").get().val())
            for id_ in times:  # USER IDS
                try:
                    for server_ in times[id_]["OSI"]:  # SERVER IDS IN USERS ID OSI
                        times[id_]["OSI"][server_]["P7D"] = 0
                except:
                    continue
            db.child("TIMINGS").set(times)
            await self.BOT_CHN.send(
                f"> `[OSI]` reset last 7 days timer at `{datetime.now(timezone('GMT'))} GMT`"
            )
        elif which == "month":
            times = dict(db.child("TIMINGS").get().val())
            for id_ in times:  # USER IDS
                try:
                    for server_ in times[id_]["OSI"]:  # SERVER IDS IN USERS ID OSI
                        times[id_]["OSI"][server_]["P1M"] = 0
                except:
                    continue
            db.child("TIMINGS").set(times)
            await self.BOT_CHN.send(
                f"> `[OSI]` reset last 1 months timer at `{datetime.now(timezone('GMT'))} GMT`"
            )
        else:
            await ctx.send("day | week | month")


def setup(bot):
    bot.add_cog(OSI(bot))
    print("---> OSI LOADED")
