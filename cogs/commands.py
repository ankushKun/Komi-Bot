import discord
from discord.ext import commands
from collections import OrderedDict
from datetime import datetime
from pytz import timezone
import json
from decouple import config as env
from DiscordUtils.Pagination import AutoEmbedPaginator

LEVELS = [10, 50, 100, 200, 300, 400, 500, 1000, 2000, 5000]

with open("config.json", "r") as read_file:
    config = json.load(read_file)

import pyrebase

if config["USE_FIREBASE_JSON"] == 1:  # 0 to use env, 1 to use json
    with open("firebase.json", "r") as read_file:
        firebase = pyrebase.initialize_app(json.load(read_file))
else:
    firebase = pyrebase.initialize_app(json.loads(env("FIREBASE_CONFIG")))
db = firebase.database()

SERVERS = config["INTEGRATIONS"]

""" DATABASE STRUCTURE
TIMINGS:
    USER_ID:
        TOTAL:int
        P24H:int
        P7D:int
        P1M:int
        OSI:
            GUILD_IDS:
                TOTAL:int
                P24H:int
                P7D:int
                P1M:int
"""

# CONVERTS MINUTES INTO HOURS,MINUTES
def mins_hours(mins: int):
    hours = int(mins / 60)
    minutes = mins % 60
    return hours, minutes


class Cmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.GUILD = self.bot.get_guild(config["GUILD_ID"])
        self.BOT_CHANNEL = self.GUILD.get_channel(
            config["CHANNELS"]["TEXT"]["KOMI_MESSAGES"]
        )
        level = config["ROLES"]["LEVEL"]
        self.LEVEL_ROLES = []
        for lvl in level:
            self.LEVEL_ROLES.append(self.GUILD.get_role(level[lvl]))

    @commands.command(aliases=["studytime", "st"])
    async def stats(self, ctx, user: discord.User = None):
        if user == None:
            user = ctx.author
        t = db.child("TIMINGS").child(user.id).get().val()
        if t == None:
            total, daily, weekly, monthly = (0, 0), (0, 0), (0, 0), (0, 0)
        else:
            total, daily, weekly, monthly = (
                mins_hours(t["TOTAL"]),
                mins_hours(t["P24H"]),
                mins_hours(t["P7D"]),
                mins_hours(t["P1M"]),
            )

            desc = f"Total : {total[0]} Hrs {total[1]} Mins\nToday : {daily[0]} Hrs {daily[1]} Mins\nThis Week : {weekly[0]} Hrs {weekly[1]} Mins\nThis month : {monthly[0]} Hrs {monthly[1]} Mins"
            emb1 = discord.Embed(
                title=f"STATS FOR {user} in Komi San wants you to study",
                description=f"```\n{desc}\n```",
                color=0xFFFFFF,
            )

            OSI = db.child("TIMINGS").child(user.id).child("OSI").get().val()
            if OSI == None:
                await ctx.send(embed=emb1)
                return
            else:
                time_embeds = [emb1]
                paginator = AutoEmbedPaginator(ctx)
                for guild_id in OSI:
                    total, daily, weekly, monthly = (
                        mins_hours(OSI[guild_id]["TOTAL"]),
                        mins_hours(OSI[guild_id]["P24H"]),
                        mins_hours(OSI[guild_id]["P7D"]),
                        mins_hours(OSI[guild_id]["P1M"]),
                    )

                    desc = f"Total : {total[0]} Hrs {total[1]} Mins\nToday : {daily[0]} Hrs {daily[1]} Mins\nThis Week : {weekly[0]} Hrs {weekly[1]} Mins\nThis month : {monthly[0]} Hrs {monthly[1]} Mins"
                    emb = discord.Embed(
                        title=f"STATS FOR {user} in {SERVERS[str(guild_id)]['NAME']}",
                        description=f"```\n{desc}\n```",
                        color=0xFFFFFF,
                    )
                    time_embeds.append(emb)
                await paginator.run(time_embeds)

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx, timer="DAY"):
        timer = timer.upper()
        if timer in ("TOTAL", "ALL"):
            t = "TOTAL"
        elif timer in ("MONTH", "MONTHLY", "M"):
            t = "P1M"
        elif timer in ("WEEK", "WEEKLY", "W"):
            t = "P7D"
        elif timer in ("DAY", "DAILY", "D"):
            t = "P24H"
        else:
            t = "P24H"

        lb = db.child("TIMINGS").order_by_child(t).get().val()
        if lb == None:
            await ctx.send(f"{timer} leaderboard empty")
            return
        lb = OrderedDict(reversed(list(lb.items())))  # REVERSE THE SORTED DICT
        desc = f""
        for mem_id in lb:
            try:
                member = await self.GUILD.fetch_member(mem_id)
            except Exception:
                member = "UNKNOWN MEMBER"
            hrs, mins = mins_hours(lb[mem_id][t])
            position = list(lb.keys()).index(mem_id) + 1
            if position > 10:
                break
            if mem_id == str(ctx.author.id):
                desc += f"-> | {member} | {hrs} Hrs {mins} Mins <-\n"
            else:
                if position == 10:  # ONE SPACE LESSER
                    desc += f"#{position}| {member} | {hrs} Hrs {mins} Mins\n"
                else:
                    desc += f"#{position} | {member} | {hrs} Hrs {mins} Mins\n"

        mem_id = str(ctx.author.id)
        try:
            member = await self.GUILD.fetch_member(mem_id)
            hrs, mins = mins_hours(lb[mem_id][t])
            position = list(lb.keys()).index(mem_id) + 1
        except Exception:
            member = "UNKNOWN MEMBER"
            hrs, mins = 0, 0
            position = "NA"

        emb = discord.Embed(
            title=f"**LEADERBOARD [{timer}]**",
            description=f"```\n{desc}\n```",
            color=0xFFFFFF,
        )
        emb.set_author(name="available options : total, day, week, month")
        emb.set_footer(text=f"#{position} | {member} | {hrs} Hrs {mins} Mins")
        await ctx.send(embed=emb)

    @commands.command()
    @commands.is_owner()
    async def manualreset(self, ctx, which):
        if which == "day":
            times = dict(db.child("TIMINGS").get().val())
            for id_ in times:
                times[id_]["P24H"] = 0
            db.child("TIMINGS").set(times)
            await self.BOT_CHANNEL.send(
                f"> manual reset last 24 hours timer at `{datetime.now(timezone('GMT'))} GMT`"
            )
        elif which == "week":
            times = dict(db.child("TIMINGS").get().val())
            for id_ in times:
                times[id_]["P7D"] = 0
            db.child("TIMINGS").set(times)
            await self.BOT_CHANNEL.send(
                f"> manual reset last 7 days timer at `{datetime.now(timezone('GMT'))} GMT`"
            )
        elif which == "month":
            times = dict(db.child("TIMINGS").get().val())
            for id_ in times:
                times[id_]["P1M"] = 0
            db.child("TIMINGS").set(times)
            await self.BOT_CHANNEL.send(
                f"> manual reset last 1 months timer at `{datetime.now(timezone('GMT'))} GMT`"
            )
        else:
            await ctx.send("day | week | month")

    @commands.command()
    @commands.is_owner()
    async def updatelevels(self, ctx, m: discord.Member):
        t = db.child("TIMINGS").child(m.id).get().val()
        if t != None:
            time = t["TOTAL"]
            hours, _ = mins_hours(time)
            for r in LEVELS:
                if hours <= r:
                    pos = LEVELS.index(r) - 1
                    if pos < 0:
                        pos = 0
                    print(hours, r, pos)
                    role_to_give = self.LEVEL_ROLES[pos]
                    for role in self.LEVEL_ROLES:
                        await m.remove_roles(role)
                    await m.add_roles(role_to_give)
                    break
            await ctx.send(f"> updated level roles for {m}")
        else:
            await ctx.send(f"> {m} is not in the database")


def setup(bot):
    bot.add_cog(Cmds(bot))
    print("---> COMMANDS LOADED")
