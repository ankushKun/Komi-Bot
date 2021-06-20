import discord
from discord.ext import commands
import calendar
from datetime import datetime
from pytz import timezone



class Help(commands.Cog):
    def __init__(self,bot):
        self.bot=bot

    @commands.command()
    async def help(self,ctx):
        now = datetime.now(timezone("GMT"))
        last_day = calendar.monthrange(now.year,now.month)[1]
        dsc=f"""
prefix : `\`

`studytime`
aliases = [`st`]
shows the time spent in study channels for the past 24 hours, 7 days and 1 month

`leaderboard`
aliases = [`lb`]
shows the top 10 users dominating study channels


daily reset - Everyday 12AM GMT | {23-now.hour} hours left
weekly reset - Monday 12AM GMT | {7-now.weekday()} days left
monthly reset - First day of the month 12AM GMT | {last_day-now.day} days left

"""
        emb = discord.Embed(title="Komi~San sent help",description=dsc,color=0xFFFFFF)
        await ctx.send(embed=emb)

def setup(bot):
    bot.add_cog(Help(bot))
    print('---> HELP LOADED')