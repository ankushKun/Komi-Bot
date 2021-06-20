from cogs.commands import mins_hours
import discord
from discord.ext import commands, tasks
from datetime import datetime
from pytz import timezone
import json

LEVELS = [10, 50, 100, 200, 300, 400, 500, 1000, 2000, 5000]

with open("config.json", "r") as read_file:
    config = json.load(read_file)

import pyrebase

if config["USE_FIREBASE_JSON"] == 1:  # 0 to use env, 1 to use json
    with open("firebase.json", "r") as read_file:
        firebase = pyrebase.initialize_app(json.load(read_file))
else:
    firebase = pyrebase.initialize_app(json.load(env("FIREBASE_CONFIG")))
db = firebase.database()

""" DATABASE STRUCTURE
TIMINGS:
    USER_ID:
        TOTAL:int
        P24H:int
        P7D:int
        P1M:int
"""


class Timers(commands.Cog):
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

        level = config["ROLES"]["LEVEL"]
        self.LEVEL_ROLES = []
        for lvl in level:
            self.LEVEL_ROLES.append(self.GUILD.get_role(level[lvl]))

        self.update_counter.start()
        self.add_minutes.start()
        self.reset.start()
        self.started = False

    def get_vc_members(self):
        members = []
        for vc in self.GUILD.voice_channels:
            if vc.category_id in config["CATEGORY"].values():
                if vc.category_id == config["CATEGORY"]["EXTRACURRICULAR"]:
                    for mem in vc.members:
                        if mem.voice.self_stream or mem.voice.self_video:
                            members.append(mem)
                else:
                    for mem in vc.members:
                        if not mem.bot:
                            members.append(mem)
        for vc in self.GUILD.stage_channels:
            if vc.category_id in config["CATEGORY"].values():
                members += vc.members
        return members

    async def add_time(self, m: discord.Member):
        mins_to_add = config["TIMER_INTERVAL"]
        t = db.child("TIMINGS").child(m.id).get().val()
        if t == None:
            db.child("TIMINGS").child(m.id).set(
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
            db.child("TIMINGS").child(m.id).set(t)

            # UPDATE LEVEL ROLES
            total = t["TOTAL"]
            hours, _ = mins_hours(total)
            for r in LEVELS:
                if hours <= r:
                    pos = LEVELS.index(r) - 1
                    if pos < 0:
                        pos = 0
                    role_to_give = self.LEVEL_ROLES[pos]
                    break
            for role in self.LEVEL_ROLES:
                await m.remove_roles(role)
            await m.add_roles(role_to_give)

    ################# LOOPS #################

    @tasks.loop(minutes=30)
    async def reset(self):
        now = datetime.now(timezone("GMT"))
        if now.hour == 0:
            times = dict(db.child("TIMINGS").get().val())
            for id_ in times:
                times[id_]["P24H"] = 0
            db.child("TIMINGS").set(times)
            await self.BOT_CHANNEL.send(
                f"> reset last 24 hours timer at `{datetime.now(timezone('GMT'))} GMT`"
            )
            if now.weekday() == 0:
                times = dict(db.child("TIMINGS").get().val())
                for id_ in times:
                    times[id_]["P7D"] = 0
                db.child("TIMINGS").set(times)
                await self.BOT_CHANNEL.send(
                    f"> reset last 7 days timer at `{datetime.now(timezone('GMT'))} GMT`"
                )
            if now.day == 1:
                times = dict(db.child("TIMINGS").get().val())
                for id_ in times:
                    times[id_]["P1M"] = 0
                db.child("TIMINGS").set(times)
                await self.BOT_CHANNEL.send(
                    f"> reset last 1 months timer at `{datetime.now(timezone('GMT'))} GMT`"
                )

    @tasks.loop(seconds=15)
    async def update_counter(self):
        count = len(self.get_vc_members())
        await self.COUNTER.edit(name=f"now studying : {count} users")

    @tasks.loop(minutes=config["TIMER_INTERVAL"])
    async def add_minutes(self):
        if not self.started:
            self.started = True
            return
        now_studying = self.get_vc_members()
        for member in now_studying:
            if not member.bot:
                await self.add_time(member)
        await self.BOT_CHANNEL.send(
            f"> updated timings [`{datetime.now(timezone('GMT'))} GMT`]"
        )

    #########################################


def setup(bot):
    bot.add_cog(Timers(bot))
    print("---> TIMERS LOADED")
