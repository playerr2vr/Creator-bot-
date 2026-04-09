import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import timedelta, datetime
import re
import os
from dotenv import load_dotenv
import random
import asyncio
import aiohttp

# Load token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

warnings = {}
automod_enabled = False
reminders = {}

# ================= BAD WORD FILTER =================
bad_words = ["nigga", "nigger", "fuck"]  # Replace responsibly

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
@tree.command(name="ban", description="Ban a member from the server")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member):
    await member.ban()
    await interaction.response.send_message(f"{member} banned.")

@tree.command(name="kick", description="Kick a member from the server")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member):
    await member.kick()
    await interaction.response.send_message(f"{member} kicked.")

@tree.command(name="warn", description="Warn a member and track their warnings")
async def warn(interaction: discord.Interaction, member: discord.Member):
    uid = str(member.id)
    warnings[uid] = warnings.get(uid, 0) + 1
    await interaction.response.send_message(f"{member} has {warnings[uid]} warnings.")

@tree.command(name="warnings", description="Check the number of warnings a member has")
async def check_warnings(interaction: discord.Interaction, member: discord.Member):
    uid = str(member.id)
    await interaction.response.send_message(f"{member} has {warnings.get(uid, 0)} warnings.")

@tree.command(name="clearwarnings", description="Clear all warnings of a member")
async def clear_warnings(interaction: discord.Interaction, member: discord.Member):
    warnings[str(member.id)] = 0
    await interaction.response.send_message(f"{member}'s warnings cleared.")

@tree.command(name="mute", description="Mute a member for a specific duration (e.g., 10s,5m,1h,1d)")
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

@tree.command(name="purge", description="Delete a number of messages from a channel")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"Deleted {amount} messages.", ephemeral=True)

@tree.command(name="lock", description="Lock the current channel so everyone cannot send messages")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("Channel locked.")

@tree.command(name="unlock", description="Unlock the current channel so everyone can send messages")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("Channel unlocked.")

@tree.command(name="slowmode", description="Set slowmode delay for the channel in seconds")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"Slowmode set to {seconds}s.")

@tree.command(name="nickname", description="Change the nickname of a member")
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

@tree.command(name="automod", description="Toggle automatic anti-spam filter")
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
    responses = ["Yes.", "No.", "Maybe.", "Definitely.", "I don't think so.", "Absolutely!", "Ask again later."]
    await interaction.response.send_message(f"🎱 Question: {question}\nAnswer: {random.choice(responses)}")

@tree.command(name="roll", description="Roll a dice with a given number of sides (default 6)")
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

# ================= UNIQUE COMMANDS =================
@tree.command(name="userinfo", description="Show detailed information about a member")
async def userinfo(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=f"{member}", color=discord.Color.blue())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%b %d, %Y"))
    embed.add_field(name="Roles", value=", ".join([r.name for r in member.roles if r.name != "@everyone"]))
    await interaction.response.send_message(embed=embed)

@tree.command(name="serverstats", description="Show basic statistics about the server")
async def serverstats(interaction: discord.Interaction):
    guild = interaction.guild
    total_members = guild.member_count
    online_members = len([m for m in guild.members if m.status != discord.Status.offline])
    embed = discord.Embed(title=f"{guild.name} Stats", color=discord.Color.green())
    embed.add_field(name="Total Members", value=total_members)
    embed.add_field(name="Online Members", value=online_members)
    embed.add_field(name="Roles", value=len(guild.roles))
    embed.add_field(name="Channels", value=len(guild.channels))
    embed.add_field(name="Boost Level", value=guild.premium_tier)
    await interaction.response.send_message(embed=embed)

@tree.command(name="avatar", description="Show a member's avatar")
async def avatar(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=f"{member}'s Avatar")
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@tree.command(name="remindme", description="Set a personal reminder that will DM you after a certain time")
async def remindme(interaction: discord.Interaction, time: str, *, text: str):
    duration = parse_time(time)
    if not duration:
        return await interaction.response.send_message("Invalid time format! Use 10s, 5m, 1h, 1d.", ephemeral=True)
    await interaction.response.send_message(f"Reminder set for {time}: {text}", ephemeral=True)
    await asyncio.sleep(duration.total_seconds())
    await interaction.user.send(f"⏰ Reminder: {text}")

@tree.command(name="poll", description="Create a reaction poll with up to 5 options")
async def poll(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None, option5: str = None):
    options = [option1, option2, option3, option4, option5]
    options = [o for o in options if o]
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    description = "\n".join([f"{emojis[i]} {options[i]}" for i in range(len(options))])
    embed = discord.Embed(title=question, description=description, color=discord.Color.orange())
    msg = await interaction.response.send_message(embed=embed)
    msg_obj = await interaction.original_response()
    for i in range(len(options)):
        await msg_obj.add_reaction(emojis[i])

# ================= ADDITIONAL UNIQUE COMMANDS =================
@tree.command(name="dailyquote", description="Receive a random motivational or funny quote")
async def dailyquote(interaction: discord.Interaction):
    quotes = [
        "Believe you can and you're halfway there.",
        "Do one thing every day that scares you.",
        "Stay positive, work hard, make it happen.",
        "Hustle in silence, let success make the noise.",
        "Mistakes are proof that you’re trying."
    ]
    await interaction.response.send_message(random.choice(quotes))

@tree.command(name="remindall", description="Send a reminder to a specific channel after a set time")
async def remindall(interaction: discord.Interaction, time: str, channel: discord.TextChannel, *, message_text: str):
    duration = parse_time(time)
    if not duration:
        return await interaction.response.send_message("Invalid time format!", ephemeral=True)
    await interaction.response.send_message(f"Reminder set in {channel.mention} for {time}.", ephemeral=True)
    await asyncio.sleep(duration.total_seconds())
    await channel.send(f"⏰ Reminder: {message_text}")

@tree.command(name="timer", description="Set a countdown timer in the current channel")
async def timer(interaction: discord.Interaction, time: str):
    duration = parse_time(time)
    if not duration:
        return await interaction.response.send_message("Invalid time format!", ephemeral=True)
    await interaction.response.send_message(f"Timer started for {time}.")
    await asyncio.sleep(duration.total_seconds())
    await interaction.followup.send(f"⏰ Timer for {time} is up!")

@tree.command(name="avatarcompare", description="Compare avatars of two members side by side")
async def avatarcompare(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    embed = discord.Embed(title="Avatar Compare", color=discord.Color.purple())
    embed.add_field(name=user1.display_name, value=f"[Avatar]({user1.display_avatar.url})", inline=True)
    embed.add_field(name=user2.display_name, value=f"[Avatar]({user2.display_avatar.url})", inline=True)
    await interaction.response.send_message(embed=embed)

@tree.command(name="weather", description="Show the weather for a specified city (API integration needed)")
async def weather(interaction: discord.Interaction, city: str):
    await interaction.response.send_message(f"Weather feature not set up yet for {city}.")

# ================= ERROR HANDLING =================
@tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("You don't have permission.", ephemeral=True)

bot.run(TOKEN)
