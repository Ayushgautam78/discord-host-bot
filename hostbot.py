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


        except Exception as e:
            print("Session error:", e)

        await asyncio.sleep(25)# ===== SESSION LOOP (SAFE WINDOW SYSTEM) =====
async def session_loop():
    global morning_active, evening_active
    global morning_links, evening_links

    await bot.wait_until_ready()

    warned_morning_start = False
    warned_morning_end = False
    warned_evening_start = False
    warned_evening_end = False

    while True:
        now = datetime.now(INDIA_TZ)

        # ===== MORNING TIMES =====
        morning_start = now.replace(hour=12, minute=34, second=0, microsecond=0)
        morning_end = morning_start + timedelta(hours=1)

        # --- 10 MIN WARNING START ---
        if not warned_morning_start and morning_start - timedelta(minutes=10) <= now < morning_start:
            warned_morning_start = True
            ch = bot.get_channel(MORNING_CHANNEL_ID)
            if ch:
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention} Morning session starting in 10 minutes")

        # --- START ---
        if not morning_active and morning_start <= now < morning_start + timedelta(seconds=40):
            morning_active = True
            morning_links.clear()
            warned_morning_end = False
            ch = bot.get_channel(MORNING_CHANNEL_ID)
            if ch:
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention}\nMorning session started. Drop links.")

        # --- 10 MIN END WARNING ---
        if morning_active and not warned_morning_end and morning_end - timedelta(minutes=10) <= now < morning_end:
            warned_morning_end = True
            ch = bot.get_channel(MORNING_CHANNEL_ID)
            if ch:
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention} Morning session ending in 10 minutes")

        # --- END ---
        if morning_active and now >= morning_end:
            morning_active = False
            warned_morning_start = False
            warned_morning_end = False
            ch = bot.get_channel(MORNING_CHANNEL_ID)
            if ch:
                role = ch.guild.get_role(AIR_ROLE_ID)
                total = len(morning_links)
                await ch.send(f"{role.mention}\nMorning session ended\nTotal links: {total}")

        # ===== EVENING =====
        evening_start = now.replace(hour=19, minute=0, second=0, microsecond=0)
        evening_end = evening_start + timedelta(hours=1)

        if not warned_evening_start and evening_start - timedelta(minutes=10) <= now < evening_start:
            warned_evening_start = True
            ch = bot.get_channel(EVENING_CHANNEL_ID)
            if ch:
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention} Evening session starting in 10 minutes")

        if not evening_active and evening_start <= now < evening_start + timedelta(seconds=40):
            evening_active = True
            evening_links.clear()
            warned_evening_end = False
            ch = bot.get_channel(EVENING_CHANNEL_ID)
            if ch:
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention}\nEvening session started. Drop links.")

        if evening_active and not warned_evening_end and evening_end - timedelta(minutes=10) <= now < evening_end:
            warned_evening_end = True
            ch = bot.get_channel(EVENING_CHANNEL_ID)
            if ch:
                role = ch.guild.get_role(AIR_ROLE_ID)
                await ch.send(f"{role.mention} Evening session ending in 10 minutes")

        if evening_active and now >= evening_end:
            evening_active = False
            warned_evening_start = False
            warned_evening_end = False
            ch = bot.get_channel(EVENING_CHANNEL_ID)
            if ch:
                role = ch.guild.get_role(AIR_ROLE_ID)
                total = len(evening_links)
                await ch.send(f"{role.mention}\nEvening session ended\nTotal links: {total}")

        await asyncio.sleep(20)

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
