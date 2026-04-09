import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import re
import os
from dotenv import load_dotenv
import random

# Load token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

warnings = {}
automod_enabled = False

# ================= BAD WORD FILTER =================
# Replace placeholders responsibly with any words you want filtered
bad_words = [
    "nigga", "nigger", "fuck"
]

# ================= TIME PARSER =================
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

# ================= EVENTS =================
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Automod spam filter
    if automod_enabled and message.content.count("http") > 2:
        await message.delete()
        await message.channel.send(f"{message.author.mention} no spam!", delete_after=5)

    # Bad word filter
    if any(word.lower() in message.content.lower() for word in bad_words):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, watch your language!", delete_after=5)

    await bot.process_commands(message)

# ================= MODERATION COMMANDS =================
@tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member):
    await member.ban()
    await interaction.response.send_message(f"{member} banned.")

@tree.command(name="kick", description="Kick a member")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member):
    await member.kick()
    await interaction.response.send_message(f"{member} kicked.")

@tree.command(name="warn", description="Warn a member")
async def warn(interaction: discord.Interaction, member: discord.Member):
    uid = str(member.id)
    warnings[uid] = warnings.get(uid, 0) + 1
    await interaction.response.send_message(f"{member} has {warnings[uid]} warnings.")

@tree.command(name="warnings", description="Check warnings of a member")
async def check_warnings(interaction: discord.Interaction, member: discord.Member):
    uid = str(member.id)
    await interaction.response.send_message(f"{member} has {warnings.get(uid, 0)} warnings.")

@tree.command(name="clearwarnings", description="Clear a member's warnings")
async def clear_warnings(interaction: discord.Interaction, member: discord.Member):
    warnings[str(member.id)] = 0
    await interaction.response.send_message(f"{member}'s warnings cleared.")

@tree.command(name="mute", description="Mute a member with a time (10s,5m,1h,1d)")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, time: str):
    duration = parse_time(time)
    if not duration:
        return await interaction.response.send_message("Invalid format! Use 10s,5m,1h,1d.", ephemeral=True)
    await member.timeout(duration)
    await interaction.response.send_message(f"{member} muted for {time}")

@tree.command(name="unmute", description="Unmute a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"{member} unmuted.")

@tree.command(name="purge", description="Delete multiple messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"Deleted {amount} messages.", ephemeral=True)

@tree.command(name="lock", description="Lock the current channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("Channel locked.")

@tree.command(name="unlock", description="Unlock the current channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("Channel unlocked.")

@tree.command(name="slowmode", description="Set slowmode delay in seconds")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"Slowmode set to {seconds}s.")

@tree.command(name="nickname", description="Change a member's nickname")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nickname(interaction: discord.Interaction, member: discord.Member, name: str):
    await member.edit(nick=name)
    await interaction.response.send_message(f"{member} renamed to {name}.")

@tree.command(name="role", description="Add or remove a role from a member")
@app_commands.checks.has_permissions(manage_roles=True)
async def role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if role in member.roles:
        await member.remove_roles(role)
        await interaction.response.send_message(f"Removed {role.name} from {member}.")
    else:
        await member.add_roles(role)
        await interaction.response.send_message(f"Added {role.name} to {member}.")

@tree.command(name="automod", description="Toggle anti-spam automod")
@app_commands.checks.has_permissions(manage_guild=True)
async def automod(interaction: discord.Interaction, toggle: str):
    global automod_enabled
    if toggle.lower() == "on":
        automod_enabled = True
        await interaction.response.send_message("Automod enabled.")
    else:
        automod_enabled = False
        await interaction.response.send_message("Automod disabled.")

# ================= FUN COMMANDS =================
@tree.command(name="8ball", description="Ask the magic 8-ball a question")
async def eight_ball(interaction: discord.Interaction, question: str):
    responses = [
        "Yes.", "No.", "Maybe.", "Definitely.", "I don't think so.", "Absolutely!", "Ask again later."
    ]
    await interaction.response.send_message(f"🎱 Question: {question}\nAnswer: {random.choice(responses)}")

@tree.command(name="roll", description="Roll a dice")
async def roll(interaction: discord.Interaction, sides: int = 6):
    if sides < 2:
        sides = 6
    result = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 You rolled a {result} on a {sides}-sided dice!")

@tree.command(name="say", description="Server owner only: Make the bot say something")
async def say(interaction: discord.Interaction, text: str):
    if interaction.user.id != interaction.guild.owner_id:
        return await interaction.response.send_message("Only the server owner can use this.", ephemeral=True)
    await interaction.response.send_message(text)

# ================= ERROR HANDLING =================
@tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("You don't have permission.", ephemeral=True)

bot.run(TOKEN)
