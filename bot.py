import discord
from discord.ext import commands
import re
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

warnings = {}

# ⏱ Time parser (10m, 1h, etc.)
def parse_time(time_str):
    match = re.match(r"^(\d+)(s|m|h|d)$", time_str)
    if not match:
        return None

    value, unit = match.groups()
    value = int(value)

    if unit == "s":
        return value
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 60 * 60
    if unit == "d":
        return value * 24 * 60 * 60

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# 🚫 BAN
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member):
    await member.ban()
    await ctx.send(f"{member} has been banned.")

# 👢 KICK
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member):
    await member.kick()
    await ctx.send(f"{member} has been kicked.")

# ⚠️ WARN
@bot.command()
async def warn(ctx, member: discord.Member):
    user_id = str(member.id)

    if user_id not in warnings:
        warnings[user_id] = 0

    warnings[user_id] += 1
    await ctx.send(f"{member} now has {warnings[user_id]} warning(s).")

# 🔇 MUTE (timeout)
@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, time: str):
    duration = parse_time(time)

    if duration is None:
        return await ctx.send("Use format like 10s, 5m, 1h, 1d.")

    # max 28 days
    if duration > 28 * 24 * 60 * 60:
        return await ctx.send("Max mute time is 28 days.")

    until = discord.utils.utcnow() + discord.timedelta(seconds=duration)
    await member.timeout(until)

    await ctx.send(f"{member} has been muted for {time}.")

# Run bot with token from .env
bot.run(TOKEN)
