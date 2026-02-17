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

# ===== WEEKLY SCHEDULE (BOLD + SPACING) =====
WEEKLY_REMINDERS = {
"monday": "**Super Monday**\n\n**Dawn || n/a ||**\n\n**Sentient || 9:30 PM IST geoguesser ||**\n\n**PrismaX || n/a ||**",
"tuesday": "**Tuesday**\n\n**Sentient || smashkart 9:30 PM IST ||**\n\n**Dawn || n/a ||**\n\n**PrismaX || trivia tango 8:00 PM IST ||**",
"wednesday": "**Wednesday**\n\n**Sentient || kirka 9:30 PM IST ||**\n\n**PrismaX || not applicable ||**\n\n**Dawn || n/a ||**",
"thursday": "**Thursday**\n\n**Sentient || rebus puzzle 9:30 PM IST ||**\n\n**PrismaX || fun mode 7:30 PM IST ||**\n\n**Dawn || n/a ||**",
"friday": "**Friday**\n\n**Sentient || among us 9:30 PM IST ||**\n\n**PrismaX || content clinic 7:30 PM IST ||**\n\n**Dawn || sunray ceremony 8:30 PM IST ||**",
"saturday": "**No events today. Chill.**",
"sunday": "**No events today. Rest.**"
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

        return f"""**{name} ({symbol})**
**Price:** ${price}
**24h:** {change:.2f}%
**Market Cap:** ${marketcap:,}
**FDV:** ${fdv:,}"""
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
            text = WEEKLY_REMINDERS.get(today, "**No schedule**")
            await channel.send(f"@everyone\n{text}")

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
                await channel.send(f"{role.mention}\n**Morning session started. Drop your links. Session ends in 1 hour.**")

        # MORNING END
        if morning_active and now.hour == 12 and now.minute >= 0:
            morning_active = False
            channel = bot.get_channel(MORNING_CHANNEL_ID)
            if channel:
                role = channel.guild.get_role(AIR_ROLE_ID)
                total = len(morning_links)
                engage = "Engage within 1.5 hours" if total < 15 else "Engage within 2 hours"
                await channel.send(f"{role.mention}\n**Morning session closed.**\n**Total links:** {total}\n**{engage}**")

        # EVENING START
        if now.hour == 21 and now.minute == 03 and not evening_active:
            evening_active = True
            evening_links.clear()
            channel = bot.get_channel(EVENING_CHANNEL_ID)
            if channel:
                role = channel.guild.get_role(AIR_ROLE_ID)
                await channel.send(f"{role.mention}\n**Evening session started. Drop your links. Session ends in 1 hour.**")

        # EVENING END
        if evening_active and now.hour == 21 and now.minute >= 05:
            evening_active = False
            channel = bot.get_channel(EVENING_CHANNEL_ID)
            if channel:
                role = channel.guild.get_role(AIR_ROLE_ID)
                total = len(evening_links)
                engage = "Engage within 1.5 hours" if total < 15 else "Engage within 2 hours"
                await channel.send(f"{role.mention}\n**Evening session closed.**\n**Total links:** {total}\n**{engage}**")

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

    if morning_active and message.channel.id == MORNING_CHANNEL_ID:
        await handle_link(message, morning_links)

    if evening_active and message.channel.id == EVENING_CHANNEL_ID:
        await handle_link(message, evening_links)

    if bot.user in message.mentions:
        text = message.content.lower()
        now = datetime.now(INDIA_TZ)

        for m in message.mentions:
            text = text.replace(f"<@{m.id}>", "")
            text = text.replace(f"<@!{m.id}>", "")
        text = text.strip()

        # ===== PRICE =====
        if "price" in text or "fdv" in text:
            parts = text.split()
            if len(parts) > 0:
                coin = parts[-1]
                data = get_crypto_price(coin)
                if data:
                    await message.reply(data, mention_author=False)
                else:
                    await message.reply("**Coin not found**", mention_author=False)
            return

        # ===== EVENT KEYWORDS =====
        trigger_words = [
            "event","schedule","reminder",
            "today","tomorrow","yesterday",
            "monday","tuesday","wednesday",
            "thursday","friday","saturday","sunday"
        ]

        if not any(word in text for word in trigger_words):
            return

        if "today" in text:
            day = now.strftime("%A").lower()
            await message.reply(WEEKLY_REMINDERS.get(day,"**No schedule**"), mention_author=False)
            return

        if "tomorrow" in text:
            day = (now + timedelta(days=1)).strftime("%A").lower()
            await message.reply(WEEKLY_REMINDERS.get(day,"**No schedule**"), mention_author=False)
            return

        if "yesterday" in text:
            day = (now - timedelta(days=1)).strftime("%A").lower()
            await message.reply(WEEKLY_REMINDERS.get(day,"**No schedule**"), mention_author=False)
            return

        days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        for d in days:
            if d in text:
                await message.reply(WEEKLY_REMINDERS.get(d,"**No schedule**"), mention_author=False)
                return

    await bot.process_commands(message)

# ===== LINK HANDLER =====
async def handle_link(message, storage):
    if "x.com" not in message.content and "twitter.com" not in message.content:
        return

    if "/i/status/" in message.content:
        await message.reply("**Wrong link format. Fix within 10 minutes or deleted.**", mention_author=True)

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
