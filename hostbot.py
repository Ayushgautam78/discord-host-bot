import discord
from discord.ext import commands
import requests
import os
import asyncio
from datetime import datetime, timedelta
import pytz

TOKEN = os.getenv("TOKEN")

# ===== IDs =====
REMINDER_CHANNEL_ID = 1467064531728601170
MORNING_CHANNEL_ID = 1473281660370812979
EVENING_CHANNEL_ID = 1473281732999381013
AIR_ROLE_ID = 1471207018139226175

INDIA_TZ = pytz.timezone("Asia/Kolkata")

# ===== WEEKLY SCHEDULE =====
WEEKLY_REMINDERS = {
    "monday": "Super Monday\n\nDawn || n/a ||\nSentient || 9:30 PM IST geoguesser ||\nPrismaX || n/a ||",
    "tuesday": "Tuesday\n\nSentient || smashkart 9:30 PM IST ||\nDawn || n/a ||\nPrismaX || trivia tango 8:00 PM IST ||",
    "wednesday": "Wednesday\n\nSentient || kirka 9:30 PM IST ||\nPrismaX || not applicable ||\nDawn || N/A ||",
    "thursday": "Thursday\n\nSentient || rebus puzzle 9:30 PM IST ||\nPrismaX || fun mode 7:30 PM IST ||\nDawn || n/a ||",
    "friday": "Friday\n\nSentient || among us 9:30 PM IST ||\nPrismaX || content clinic 7:30 PM IST ||\nDawn || sunray ceremony 8:30 PM IST ||",
    "saturday": "No events today. Chill.",
    "sunday": "No events today. Rest."
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== SESSION STORAGE =====
morning_active = False
evening_active = False
morning_links = set()
evening_links = set()

# ===== CRYPTO PRICE =====
def get_crypto_price(query):
    try:
        search = requests.get(f"https://api.coingecko.com/api/v3/search?query={query}").json()
        if not search["coins"]:
            return None

        coin_id = search["coins"][0]["id"]
        data = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}").json()

        name = data["name"]
        symbol = data["symbol"].upper()
        price = data["market_data"]["current_price"]["usd"]
        change = data["market_data"]["price_change_percentage_24h"]
        marketcap = data["market_data"]["market_cap"]["usd"]
        fdv = data["market_data"]["fully_diluted_valuation"]["usd"]

        return f"""{name} ({symbol})
Price: ${price}
24h: {change:.2f}%
Market Cap: ${marketcap:,}
FDV: ${fdv:,}"""
    except:
        return None

# ===== AUTO DAILY REMINDER =====
async def auto_daily_reminder():
    await bot.wait_until_ready()
    while True:
        now = datetime.now(INDIA_TZ)
        target = now.replace(hour=10, minute=0, second=0, microsecond=0)

        if now >= target:
            target += timedelta(days=1)

        await asyncio.sleep((target - now).total_seconds())

        channel = bot.get_channel(REMINDER_CHANNEL_ID)
        if channel:
            today = datetime.now(INDIA_TZ).strftime("%A").lower()
            text = WEEKLY_REMINDERS.get(today, "No schedule")
            await channel.send(f"@everyone {text}")

        await asyncio.sleep(60)

# ===== SESSION LOOP =====
async def session_loop():
    global morning_active, evening_active
    global morning_links, evening_links

    await bot.wait_until_ready()

    while True:
        now = datetime.now(INDIA_TZ)

        # MORNING START
        if now.hour == 11 and now.minute == 0 and not morning_active:
            morning_active = True
            morning_links.clear()
            channel = bot.get_channel(MORNING_CHANNEL_ID)
            if channel:
                role = channel.guild.get_role(AIR_ROLE_ID)
                await channel.send(f"{role.mention} ** session is started now. You can drop your links. Session will end in one hour. ** ")

        # MORNING END (safe trigger)
        if morning_active and now.hour == 12 and now.minute >= 0:
            morning_active = False
            channel = bot.get_channel(MORNING_CHANNEL_ID)
            if channel:
                role = channel.guild.get_role(AIR_ROLE_ID)
                total = len(morning_links)
                engage = "Engage for 1.5 hours" if total < 15 else "Engage for 2 hours"
                await channel.send(f"{role.mention}** Morning session closed.\nTotal links: {total}\n{engage}** ")

        # EVENING START
        if now.hour == 19 and now.minute == 40 and not evening_active:
            evening_active = True
            evening_links.clear()
            channel = bot.get_channel(EVENING_CHANNEL_ID)
            if channel:
                role = channel.guild.get_role(AIR_ROLE_ID)
                await channel.send(f"{role.mention} ** session is started now. You can drop your links. Session will end in one hour.** ")

        # EVENING END (FIXED — never miss)
        if evening_active and now.hour == 19 and now.minute >= 42:
            evening_active = False
            channel = bot.get_channel(EVENING_CHANNEL_ID)
            if channel:
                role = channel.guild.get_role(AIR_ROLE_ID)
                total = len(evening_links)
                engage = "Engage for 1.5 hours" if total < 15 else "Engage for 2 hours"
                await channel.send(f"{role.mention}** Evening session closed.\nTotal links: {total}\n{engage} ** ")

        await asyncio.sleep(20)

# ===== READY =====
@bot.event
async def on_ready():
    print("Bot online")
    bot.loop.create_task(auto_daily_reminder())
    bot.loop.create_task(session_loop())

# ===== MESSAGE HANDLER =====
@bot.event
async def on_message(message):
    global morning_active, evening_active

    if message.author == bot.user:
        return

    # ===== SESSION LINK TRACK =====
    if morning_active and message.channel.id == MORNING_CHANNEL_ID:
        await handle_link(message, morning_links)

    if evening_active and message.channel.id == EVENING_CHANNEL_ID:
        await handle_link(message, evening_links)

    # ===== COMMANDS WHEN TAGGED =====
    if bot.user in message.mentions:
        text = message.content.lower()

        if "price" in text or "fdv" in text:
            coin = text.split()[-1]
            data = get_crypto_price(coin)
            if data:
                await message.reply(data, mention_author=False)
            else:
                await message.reply("coin not found", mention_author=False)
            return

        if "schedule" in text or "reminder" in text or "event" in text:
            now = datetime.now(INDIA_TZ)
            today = now.strftime("%A").lower()
            reminder = WEEKLY_REMINDERS.get(today, "No schedule")
            await message.reply(reminder, mention_author=False)
            return

    await bot.process_commands(message)

# ===== LINK HANDLER =====
async def handle_link(message, storage):
    if "x.com" not in message.content and "twitter.com" not in message.content:
        return

    if "/i/status/" in message.content:
        warn = await message.reply("Wrong link format. Use username/status format. Fix within 10 minutes or deleted.", mention_author=True)

        async def delete_later():
            await asyncio.sleep(600)
            try:
                await message.delete()
            except:
                pass

        bot.loop.create_task(delete_later())
        return

    storage.add(message.content)

bot.run(TOKEN)
