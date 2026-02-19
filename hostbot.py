import discord
from discord.ext import commands
import requests
import os
import asyncio
from datetime import datetime, timedelta
import pytz
import re

TOKEN = os.getenv("TOKEN")

REMINDER_CHANNEL_ID = 1467064531728601170
MORNING_CHANNEL_ID = 1473281660370812979
EVENING_CHANNEL_ID = 1473281732999381013
AIR_ROLE_ID = 1471207018139226175

INDIA_TZ = pytz.timezone("Asia/Kolkata")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== MEMORY =====
REMINDERS = []
morning_active = False
evening_active = False
morning_links = set()
evening_links = set()

# prevent duplicate triggers
last_trigger = {}

# ===== WEEKLY EVENTS =====
WEEKLY_REMINDERS = {
"monday": "**Super Monday**\n\n**Dawn || n/a ||**\n\n**Sentient || 9:30 PM IST geoguesser ||**\n\n**PrismaX || n/a ||**",
"tuesday": "**Tuesday**\n\n**Sentient || smashkart 9:30 PM IST ||**\n\n**Dawn || n/a ||**\n\n**PrismaX || trivia tango 8:00 PM IST ||**",
"wednesday": "**Wednesday**\n\n**Sentient || kirka 9:30 PM IST ||**\n\n**PrismaX || not applicable ||**\n\n**Dawn || n/a ||**",
"thursday": "**Thursday**\n\n**Sentient || rebus puzzle 9:30 PM IST ||**\n\n**PrismaX || fun mode 7:30 PM IST ||**\n\n**Dawn || n/a ||**",
"friday": "**Friday**\n\n**Sentient || among us 9:30 PM IST ||**\n\n**PrismaX || content clinic 7:30 PM IST ||**\n\n**Dawn || sunray ceremony 8:30 PM IST ||**",
"saturday": "**No events today. Chill.**",
"sunday": "**No events today. Rest.**"
}

# ===== CRYPTO =====
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

        return f"**{name} ({symbol})**\nPrice: ${price}\n24h: {change:.2f}%\nMC: ${marketcap:,}"
    except:
        return None

# ===== PERSONAL REMINDER LOOP =====
async def reminder_loop():
    await bot.wait_until_ready()
    while True:
        now = datetime.now(INDIA_TZ).strftime("%H:%M")
        for r in REMINDERS[:]:
            if r["time"] == now:
                ch = bot.get_channel(r["channel"])
                if ch:
                    await ch.send(f"<@{r['user']}> ⏰ Reminder: {r['text']}")
                REMINDERS.remove(r)
        await asyncio.sleep(20)

# ===== DAILY 10AM SCHEDULE =====
async def daily_schedule():
    await bot.wait_until_ready()
    while True:
        now = datetime.now(INDIA_TZ)
        target = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())

        ch = bot.get_channel(REMINDER_CHANNEL_ID)
        if ch:
            today = datetime.now(INDIA_TZ).strftime("%A").lower()
            await ch.send(f"@everyone\n{WEEKLY_REMINDERS.get(today,'No schedule')}")

# ===== SESSION LOOP (SAFE WINDOW SYSTEM) =====
async def session_loop():
    global morning_active, evening_active
    await bot.wait_until_ready()

    while True:
        now = datetime.now(INDIA_TZ)
        h, m = now.hour, now.minute

        try:
            # MORNING WARNING
            if h == 12 and 31 <= m <= 52:
                ch = bot.get_channel(MORNING_CHANNEL_ID)
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention} Morning session starting in 10 minutes")
                await asyncio.sleep(70)

            # MORNING START
            if h == 12 and 32 <= m <= 2 and not morning_active:
                morning_active = True
                morning_links.clear()
                ch = bot.get_channel(MORNING_CHANNEL_ID)
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention} Morning session started. Drop links.")
                await asyncio.sleep(70)

            # MORNING END WARNING
            if h == 12 and 33 <= m <= 52:
                ch = bot.get_channel(MORNING_CHANNEL_ID)
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention} Morning session ending in 10 minutes")
                await asyncio.sleep(70)

            # MORNING END
            if h == 12 and 34 <= m <= 2 and morning_active:
                morning_active = False
                ch = bot.get_channel(MORNING_CHANNEL_ID)
                role = ch.guild.get_role(AIR_ROLE_ID)
                total = len(morning_links)
                engage = "Engage 1.5 hr" if total < 15 else "Engage 2 hr"
                await ch.send(f"{role.mention} Morning closed.\nTotal links: {total}\n{engage}")
                await asyncio.sleep(70)

            # EVENING WARNING
            if h == 18 and 50 <= m <= 52:
                ch = bot.get_channel(EVENING_CHANNEL_ID)
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention} Evening session starting in 10 minutes")
                await asyncio.sleep(70)

            # EVENING START
            if h == 19 and 0 <= m <= 2 and not evening_active:
                evening_active = True
                evening_links.clear()
                ch = bot.get_channel(EVENING_CHANNEL_ID)
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention} Evening session started. Drop links.")
                await asyncio.sleep(70)

            # EVENING END WARNING
            if h == 19 and 50 <= m <= 52:
                ch = bot.get_channel(EVENING_CHANNEL_ID)
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention} Evening session ending in 10 minutes")
                await asyncio.sleep(70)

            # EVENING END
            if h == 20 and 0 <= m <= 2 and evening_active:
                evening_active = False
                ch = bot.get_channel(EVENING_CHANNEL_ID)
                role = ch.guild.get_role(AIR_ROLE_ID)
                total = len(evening_links)
                engage = "Engage 1.5 hr" if total < 15 else "Engage 2 hr"
                await ch.send(f"{role.mention} Evening closed.\nTotal links: {total}\n{engage}")
                await asyncio.sleep(70)

        except Exception as e:
            print("Session error:", e)

        await asyncio.sleep(25)

# ===== MESSAGE HANDLER =====
@bot.event
async def on_message(message):
    global morning_links, evening_links

    if message.author == bot.user:
        return

    # LINK TRACKING
    if morning_active and message.channel.id == MORNING_CHANNEL_ID:
        await handle_link(message, morning_links)

    if evening_active and message.channel.id == EVENING_CHANNEL_ID:
        await handle_link(message, evening_links)

    if bot.user in message.mentions:
        text = message.content.lower()

        for m in message.mentions:
            text = text.replace(f"<@{m.id}>","").replace(f"<@!{m.id}>","")
        text = text.strip()

        now = datetime.now(INDIA_TZ)

        # PERSONAL REMINDER
        if "remind" in text or "set reminder" in text or "schedule" in text:
            match = re.search(r'(\d{1,2}:\d{2})', text)
            if match:
                time_val = match.group(1)
                reminder_text = text.replace(match.group(1),"").replace("remind me","").replace("set reminder","").replace("schedule","").replace("at","").strip()
                if reminder_text == "":
                    reminder_text = "Reminder"
                REMINDERS.append({
                    "user": message.author.id,
                    "time": time_val,
                    "text": reminder_text,
                    "channel": message.channel.id
                })
                await message.reply(f"Reminder set for {time_val} IST", mention_author=False)
                return

        # PRICE
        if "price" in text:
            coin = text.split()[-1]
            data = get_crypto_price(coin)
            if data:
                await message.reply(data, mention_author=False)
            else:
                await message.reply("Coin not found", mention_author=False)
            return

        # DAY EVENTS
        if "today" in text:
            day = now.strftime("%A").lower()
            await message.reply(WEEKLY_REMINDERS.get(day,"No schedule"), mention_author=False)
            return

        if "tomorrow" in text:
            day = (now + timedelta(days=1)).strftime("%A").lower()
            await message.reply(WEEKLY_REMINDERS.get(day,"No schedule"), mention_author=False)
            return

        for d in WEEKLY_REMINDERS:
            if d in text:
                await message.reply(WEEKLY_REMINDERS[d], mention_author=False)
                return

    await bot.process_commands(message)

# ===== LINK VALIDATION =====
async def handle_link(message, storage):
    if "x.com" not in message.content and "twitter.com" not in message.content:
        return

    if "/i/status/" in message.content:
        await message.reply("Wrong link format. Fix within 10 minutes or deleted.", mention_author=True)

        async def delete_later():
            await asyncio.sleep(600)
            try:
                await message.delete()
            except:
                pass

        bot.loop.create_task(delete_later())
        return

    storage.add(message.content)

@bot.event
async def on_ready():
    print("Bot stable and running")
    bot.loop.create_task(reminder_loop())
    bot.loop.create_task(session_loop())
    bot.loop.create_task(daily_schedule())

bot.run(TOKEN)
