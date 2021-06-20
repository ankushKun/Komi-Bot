import discord
from discord.ext import commands

import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFont
import os
from io import BytesIO
import requests

import json

with open("config.json", "r") as read_file:
    config = json.load(read_file)

KOMI_FONT = ImageFont.truetype("fonts/komi_writing.ttf", 65)
PFP_SIZE = (500, 500)
PFP_POS = (330, 120)

GUILD_ID = config["GUILD_ID"]
WELCOME_CHANNEL = config["CHANNELS"]["TEXT"]["WELCOME"]

WELCOME_MESSAGE = """welcome {} <a:komi_surprised:843170284184928356>
Head over to <#843086417608572948> and <#843086772966916146> to get access to the server
"""


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.guild.id == GUILD_ID:
            return
        GUILD = self.bot.get_guild(GUILD_ID)
        CHANNEL = GUILD.get_channel(WELCOME_CHANNEL)
        r = requests.get(member.avatar_url)
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        mask = Image.open("images/mask.png").convert("L")
        pfp = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
        pfp = pfp.resize(PFP_SIZE)
        mask = mask.resize(PFP_SIZE)
        pfp.putalpha(mask)

        bg_img = Image.open("images/welcome.png")
        bg_img.paste(pfp, PFP_POS, mask)

        draw_cur = ImageDraw.Draw(bg_img)

        draw_cur.text(
            (250, 650),
            str(member),
            fill=(224, 122, 255, 255),
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255),
            font=KOMI_FONT,
        )
        draw_cur.text(
            (20, 750),
            "Komi~San is happy to have you here",
            fill=(115, 115, 250, 255),
            stroke_width=3,
            font=KOMI_FONT,
            stroke_fill=(0, 0, 100, 255),
        )
        PATH = f"images/generated/{member.id}.png"
        bg_img.save(PATH)
        image_file = discord.File(PATH)
        await CHANNEL.send(WELCOME_MESSAGE.format(member.mention), file=image_file)
        os.remove("PATH")


def setup(bot):
    bot.add_cog(Welcome(bot))
    print("---> WELCOME LOADED")
