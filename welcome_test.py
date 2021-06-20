import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFont
import os
from io import BytesIO
import requests

KOMI_FONT = ImageFont.truetype("fonts/komi_writing.ttf", 65)

PFP_URL = "https://cdn.discordapp.com/avatars/666578281142812673/db016f420b75b2b1d65d1ff54ac6570e.png?size=256"
PFP_SIZE = (500, 500)
PFP_POS = (330, 120)

r = requests.get(PFP_URL)
img = Image.open(BytesIO(r.content))
mask = Image.open("images/mask.png").convert("L")
pfp = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
pfp = pfp.resize(PFP_SIZE)
mask = mask.resize(PFP_SIZE)
pfp.putalpha(mask)

bg_img = Image.open("images/welcome.png")
bg_img.paste(pfp, PFP_POS, pfp)

draw_cur = ImageDraw.Draw(bg_img)

draw_cur.text(
    (250, 650),
    f"weeblet~kun#0039",
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


bg_img.save("ok.png")