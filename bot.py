import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import timedelta, datetime, timezone
import re
import os
from dotenv import load_dotenv
import random
import asyncio

# ================= SETUP =================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

warnings = {}
automod_enabled = {}
bad_words = ["nigga", "nigger", "fuck"]
ignored_users = set()

# ================= TIME PARSER =================
def parse_time(time_str):
    match = re.match(r"^(\d+)(s|m|h|d)$", time_str)
    if not match:
        return None
    value, unit = match.groups()
    value = int(value)
    return {
        "s": timedelta(seconds=value),
        "m": timedelta(minutes=value),
        "h": timedelta(hours=value),
        "d": timedelta(days=value),
    }[unit]

# ================= EVENTS =================
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Automod spam
    if automod_enabled.get(message.guild.id):
        if message.content.count("http") > 2:
            await message.delete()
            await message.channel.send(f"{message.author.mention} no spam!", delete_after=5)

    # Bad word filter
    if message.author.id not in ignored_users:
        if any(re.search(rf"\b{word}\b", message.content, re.IGNORECASE) for word in bad_words):
            await message.delete()
            await message.channel.send(f"{message.author.mention}, watch your language!", delete_after=5)

    await bot.process_commands(message)

# ================= MODERATION =================
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

@tree.command(name="warn", description="Warn a member and track warnings")
async def warn(interaction: discord.Interaction, member: discord.Member):
    uid = str(member.id)
    warnings[uid] = warnings.get(uid, 0) + 1
    await interaction.response.send_message(f"{member} has {warnings[uid]} warnings.")

@tree.command(name="warnings", description="Check how many warnings a member has")
async def check_warnings(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"{member} has {warnings.get(str(member.id), 0)} warnings.")

@tree.command(name="clearwarnings", description="Clear all warnings for a member")
async def clear_warnings(interaction: discord.Interaction, member: discord.Member):
    warnings[str(member.id)] = 0
    await interaction.response.send_message(f"{member}'s warnings cleared.")

@tree.command(name="mute", description="Mute a member for a time (10s, 5m, 1h, 1d)")
async def mute(interaction: discord.Interaction, member: discord.Member, time: str):
    duration = parse_time(time)
    if not duration:
        return await interaction.response.send_message("Invalid format.", ephemeral=True)

    until = datetime.now(timezone.utc) + duration
    await member.timeout(until)
    await interaction.response.send_message(f"{member} muted for {time}")

@tree.command(name="unmute", description="Unmute a member")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"{member} unmuted.")

# ================= BAD WORD COMMANDS =================
@tree.command(name="listbadwords", description="List all filtered bad words")
async def list_badwords(interaction: discord.Interaction):
    await interaction.response.send_message(", ".join(bad_words) if bad_words else "No bad words set.")

@tree.command(name="addbadword", description="Add a word to the filter")
async def add_badword(interaction: discord.Interaction, word: str):
    bad_words.append(word.lower())
    await interaction.response.send_message(f"Added `{word}`")

@tree.command(name="clearbadwords", description="Clear all bad words")
async def clear_badwords(interaction: discord.Interaction):
    bad_words.clear()
    await interaction.response.send_message("Cleared bad words.")

@tree.command(name="ignore_user_badword", description="Ignore a user from bad word filter")
async def ignore_user(interaction: discord.Interaction, member: discord.Member):
    ignored_users.add(member.id)
    await interaction.response.send_message(f"{member} is ignored.")

# ================= FUN =================
@tree.command(name="coinflip", description="Flip a coin")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(["Heads", "Tails"]))

@tree.command(name="roll", description="Roll a dice")
async def roll(interaction: discord.Interaction, sides: int = 6):
    await interaction.response.send_message(f"You rolled {random.randint(1, sides)}")

@tree.command(name="8ball", description="Ask the magic 8-ball a question")
async def eight_ball(interaction: discord.Interaction, question: str):
    responses = ["Yes", "No", "Maybe", "Definitely", "Ask later"]
    await interaction.response.send_message(random.choice(responses))

# ================= 20 RARE COMMANDS =================
@tree.command(name="reverse", description="Reverse your text")
async def reverse(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(text[::-1])

@tree.command(name="mock", description="Mock text LiKe ThIs")
async def mock(interaction: discord.Interaction, text: str):
    await interaction.response.send_message("".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(text)))

@tree.command(name="choose", description="Pick a random option")
async def choose(interaction: discord.Interaction, options: str):
    choices = options.split(",")
    await interaction.response.send_message(random.choice(choices))

@tree.command(name="repeat", description="Repeat your message")
async def repeat(interaction: discord.Interaction, text: str, times: int):
    await interaction.response.send_message((text + "\n") * min(times, 5))

@tree.command(name="rate", description="Rate something 1-10")
async def rate(interaction: discord.Interaction, thing: str):
    await interaction.response.send_message(f"{thing} is {random.randint(1,10)}/10")

@tree.command(name="rng", description="Generate a random number")
async def rng(interaction: discord.Interaction, min: int, max: int):
    await interaction.response.send_message(random.randint(min, max))

@tree.command(name="clap", description="Add 👏 between words")
async def clap(interaction: discord.Interaction, text: str):
    await interaction.response.send_message("👏".join(text.split()))

@tree.command(name="leet", description="Convert text to leetspeak")
async def leet(interaction: discord.Interaction, text: str):
    table = str.maketrans("aeiot", "43107")
    await interaction.response.send_message(text.translate(table))

@tree.command(name="caps", description="Make text uppercase")
async def caps(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(text.upper())

@tree.command(name="lower", description="Make text lowercase")
async def lower(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(text.lower())

@tree.command(name="count", description="Count characters in text")
async def count(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(f"{len(text)} characters")

@tree.command(name="shuffle", description="Shuffle words")
async def shuffle(interaction: discord.Interaction, text: str):
    words = text.split()
    random.shuffle(words)
    await interaction.response.send_message(" ".join(words))

@tree.command(name="palindrome", description="Check if text is a palindrome")
async def palindrome(interaction: discord.Interaction, text: str):
    t = text.replace(" ", "").lower()
    await interaction.response.send_message("Yes" if t == t[::-1] else "No")

@tree.command(name="mathadd", description="Add two numbers")
async def mathadd(interaction: discord.Interaction, a: int, b: int):
    await interaction.response.send_message(a + b)

@tree.command(name="mathmul", description="Multiply two numbers")
async def mathmul(interaction: discord.Interaction, a: int, b: int):
    await interaction.response.send_message(a * b)

@tree.command(name="randomletter", description="Get a random letter")
async def randomletter(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice("abcdefghijklmnopqrstuvwxyz"))

@tree.command(name="randomcolor", description="Generate a random hex color")
async def randomcolor(interaction: discord.Interaction):
    await interaction.response.send_message(f"#{random.randint(0, 0xFFFFFF):06x}")

@tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"{round(bot.latency * 1000)}ms")

@tree.command(name="time", description="Show current UTC time")
async def time_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

@tree.command(name="countdown", description="Simple countdown")
async def countdown(interaction: discord.Interaction, seconds: int):
    await interaction.response.send_message(f"Counting down {seconds}s...")
    await asyncio.sleep(min(seconds, 10))
    await interaction.followup.send("Done!")

# ================= RUN =================
bot.run(TOKEN)
