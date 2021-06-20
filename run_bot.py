import discord
from discord.ext import commands
import os
from keep_alive import keep_alive
import json
from datetime import datetime
from pytz import timezone
from decouple import config as env


BOT_TOKEN = env("BOT_TOKEN")
BOT_PREFIX = env("BOT_PREFIX")

with open("config.json", "r") as read_file:
    config = json.load(read_file)

print("---> BOT is waking up\n")

intents = discord.Intents.all()
intents.typing = True
intents.presences = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=BOT_PREFIX, case_insensitive=True, intents=intents)
bot.remove_command("help")


def unload_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py") and not file.startswith("_"):
            try:
                bot.unload_extension(f"cogs.{file[:-3]}")
            except Exception as e:
                print(f"COG UNLOAD ERROR : {e}")


def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py") and not file.startswith("_"):
            try:
                bot.load_extension(f"cogs.{file[:-3]}")
            except Exception as e:
                print(f"COG LOAD ERROR : {e}")


@bot.event
async def on_ready():
    print(f"---> Logged in as : {bot.user.name} , ID : {bot.user.id}")
    print(f"prefix : {BOT_PREFIX}")
    print(f"---> Total Servers : {len(bot.guilds)}\n")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name="my friends study [\]"
        )
    )
    load_cogs()
    print("\n---> BOT is awake\n")
    guild = bot.get_guild(config["GUILD_ID"])
    channel = guild.get_channel(config["CHANNELS"]["TEXT"]["KOMI_MESSAGES"])
    await channel.send(f"> online on `{datetime.now(timezone('GMT'))} GMT`")


@bot.command(aliases=["reload"])
@commands.is_owner()
async def reload_cogs(ctx):
    unload_cogs()
    await ctx.send("> Komi san unloaded cogs")
    load_cogs()
    await ctx.send("> Komi san loaded cogs")


keep_alive()
bot.run(BOT_TOKEN)