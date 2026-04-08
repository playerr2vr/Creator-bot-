import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import re
import os
from dotenv import load_dotenv

#  Load token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

warnings = {}

#  Time parser (10m, 1h, etc.)
def parse_time(time_str):
    match = re.match(r"^(\d+)(s|m|h|d)$", time_str)
    if not match:
        return None

    value, unit = match.groups()
    value = int(value)

    if unit == "s":
        return timedelta(seconds=value)
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)

#  When bot is ready
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

#  BAN
@tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member):
    await member.ban()
    await interaction.response.send_message(f"{member} has been banned.")

#  KICK
@tree.command(name="kick", description="Kick a member")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member):
    await member.kick()
    await interaction.response.send_message(f"{member} has been kicked.")

#  WARN
@tree.command(name="warn", description="Warn a member")
async def warn(interaction: discord.Interaction, member: discord.Member):
    user_id = str(member.id)

    if user_id not in warnings:
        warnings[user_id] = 0

    warnings[user_id] += 1

    await interaction.response.send_message(
        f"{member} now has {warnings[user_id]} warning(s)."
    )

#  MUTE (custom time)
@tree.command(name="mute", description="Mute a member (e.g. 10m, 1h)")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, time: str):
    duration = parse_time(time)

    if duration is None:
        return await interaction.response.send_message(
            "Invalid format! Use 10s, 5m, 1h, 1d.",
            ephemeral=True
        )

    if duration > timedelta(days=28):
        return await interaction.response.send_message(
            "Max mute time is 28 days.",
            ephemeral=True
        )

    await member.timeout(duration)

    await interaction.response.send_message(
        f"{member} has been muted for {time}."
    )

#  Permission error handlingr
@ban.error
@kick.error
@mute.error
async def mod_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "You don't have permission to use this command.",
            ephemeral=True
        )

#  Run bot
bot.run(TOKEN)
