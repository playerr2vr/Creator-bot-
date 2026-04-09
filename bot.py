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
bad_words = ["nword", "nword1", "nword2"]  # Replace responsibly

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
@tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member):
    await member.ban()
    await interaction.response.send_message(f"{member} banned.")

@tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member):
    await member.kick()
    await interaction.response.send_message(f"{member} kicked.")

@tree.command(name="warn")
async def warn(interaction: discord.Interaction, member: discord.Member):
    uid = str(member.id)
    warnings[uid] = warnings.get(uid, 0) + 1
    await interaction.response.send_message(f"{member} has {warnings[uid]} warnings.")

@tree.command(name="warnings")
async def check_warnings(interaction: discord.Interaction, member: discord.Member):
    uid = str(member.id)
    await interaction.response.send_message(f"{member} has {warnings.get(uid, 0)} warnings.")

@tree.command(name="clearwarnings")
async def clear_warnings(interaction: discord.Interaction, member: discord.Member):
    warnings[str(member.id)] = 0
    await interaction.response.send_message(f"{member}'s warnings cleared.")

@tree.command(name="mute")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, time: str):
    duration = parse_time(time)
    if not duration:
        return await interaction.response.send_message("Invalid format! Use 10s,5m,1h,1d.", ephemeral=True)
    await member.timeout(duration)
    await interaction.response.send_message(f"{member} muted for {time}")

@tree.command(name="unmute")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"{member} unmuted.")

@tree.command(name="purge")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"Deleted {amount} messages.", ephemeral=True)

@tree.command(name="lock")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("Channel locked.")

@tree.command(name="unlock")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("Channel unlocked.")

@tree.command(name="slowmode")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"Slowmode set to {seconds}s.")

@tree.command(name="nickname")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nickname(interaction: discord.Interaction, member: discord.Member, name: str):
    await member.edit(nick=name)
    await interaction.response.send_message(f"{member} renamed to {name}.")

@tree.command(name="role")
@app_commands.checks.has_permissions(manage_roles=True)
async def role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if role in member.roles:
        await member.remove_roles(role)
        await interaction.response.send_message(f"Removed {role.name} from {member}.")
    else:
        await member.add_roles(role)
        await interaction.response.send_message(f"Added {role.name} to {member}.")

@tree.command(name="automod")
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
@tree.command(name="8ball")
async def eight_ball(interaction: discord.Interaction, question: str):
    responses = ["Yes.", "No.", "Maybe.", "Definitely.", "I don't think so.", "Absolutely!", "Ask again later."]
    await interaction.response.send_message(f"🎱 Question: {question}\nAnswer: {random.choice(responses)}")

@tree.command(name="roll")
async def roll(interaction: discord.Interaction, sides: int = 6):
    if sides < 2:
        sides = 6
    result = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 You rolled a {result} on a {sides}-sided dice!")

@tree.command(name="say")
async def say(interaction: discord.Interaction, text: str):
    if interaction.user.id != interaction.guild.owner_id:
        return await interaction.response.send_message("Only the server owner can use this.", ephemeral=True)
    await interaction.response.send_message(text)

# ================= UNIQUE COMMANDS =================
@tree.command(name="userinfo")
async def userinfo(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=f"{member}", color=discord.Color.blue())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%b %d, %Y"))
    embed.add_field(name="Roles", value=", ".join([r.name for r in member.roles if r.name != "@everyone"]))
    await interaction.response.send_message(embed=embed)

@tree.command(name="serverstats")
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

@tree.command(name="avatar")
async def avatar(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=f"{member}'s Avatar")
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@tree.command(name="remindme")
async def remindme(interaction: discord.Interaction, time: str, *, text: str):
    duration = parse_time(time)
    if not duration:
        return await interaction.response.send_message("Invalid time format! Use 10s, 5m, 1h, 1d.", ephemeral=True)
    await interaction.response.send_message(f"Reminder set for {time}: {text}", ephemeral=True)
    await asyncio.sleep(duration.total_seconds())
    await interaction.user.send(f"⏰ Reminder: {text}")

@tree.command(name="poll")
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

# ================= NEW UNIQUE COMMANDS =================
@tree.command(name="dailyquote")
async def dailyquote(interaction: discord.Interaction):
    quotes = [
        "Believe you can and you're halfway there.",
        "Do one thing every day that scares you.",
        "Stay positive, work hard, make it happen.",
        "Hustle in silence, let success make the noise.",
        "Mistakes are proof that you’re trying."
    ]
    await interaction.response.send_message(random.choice(quotes))

@tree.command(name="remindall")
async def remindall(interaction: discord.Interaction, time: str, channel: discord.TextChannel, *, message_text: str):
    duration = parse_time(time)
    if not duration:
        return await interaction.response.send_message("Invalid time format!", ephemeral=True)
    await interaction.response.send_message(f"Reminder set in {channel.mention} for {time}.", ephemeral=True)
    await asyncio.sleep(duration.total_seconds())
    await channel.send(f"⏰ Reminder: {message_text}")

@tree.command(name="timer")
async def timer(interaction: discord.Interaction, time: str):
    duration = parse_time(time)
    if not duration:
        return await interaction.response.send_message("Invalid time format!", ephemeral=True)
    await interaction.response.send_message(f"Timer started for {time}.")
    await asyncio.sleep(duration.total_seconds())
    await interaction.followup.send(f"⏰ Timer for {time} is up!")

@tree.command(name="avatarcompare")
async def avatarcompare(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    embed = discord.Embed(title="Avatar Compare", color=discord.Color.purple())
    embed.set_field_at(0, name=user1.display_name, value="[Avatar](" + user1.display_avatar.url + ")", inline=True)
    embed.set_field_at(1, name=user2.display_name, value="[Avatar](" + user2.display_avatar.url + ")", inline=True)
    embed.set_image(url="https://i.imgur.com/placeholder.png")  # Optional placeholder image if needed
    await interaction.response.send_message(embed=embed)

@tree.command(name="weather")
async def weather(interaction: discord.Interaction, city: str):
    async with aiohttp.ClientSession() as session:
        # Placeholder API; replace with actual weather API key if desired
        await interaction.response.send_message(f"Weather feature not set up yet for {city}.")
    
# ================= ERROR HANDLING =================
@tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("You don't have permission.", ephemeral=True)

bot.run(TOKEN)
