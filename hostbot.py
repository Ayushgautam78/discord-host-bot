import discord
from discord.ext import commands
import requests
import os
import asyncio
from datetime import datetime, timedelta
import pytz

TOKEN = os.getenv("TOKEN")

# ===== PUT YOUR REMINDER CHANNEL ID HERE =====
REMINDER_CHANNEL_ID = 1467064531728601170  

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

# ===== AUTO 10AM DAILY REMINDER =====
async def auto_daily_reminder():
    await bot.wait_until_ready()

    while not bot.is_closed():
        now = datetime.now(INDIA_TZ)
        target = now.replace(hour=10, minute=0, second=0, microsecond=0)

        if now >= target:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        try:
            channel = bot.get_channel(REMINDER_CHANNEL_ID)
            if channel:
                today = datetime.now(INDIA_TZ).strftime("%A").lower()
                reminder_text = WEEKLY_REMINDERS.get(today, "No schedule today")

                await channel.send(f"@everyone {reminder_text}")
                print("10AM reminder sent")
        except Exception as e:
            print("Reminder error:", e)

        await asyncio.sleep(60)

# ===== READY =====
@bot.event
async def on_ready():
    print("Hosting bot online")
    bot.loop.create_task(auto_daily_reminder())

# ===== MESSAGE HANDLER =====
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        text = message.content.lower()

        # ===== PRICE =====
        if "price" in text or "fdv" in text:
            coin = text.split()[-1]
            data = get_crypto_price(coin)

            if data:
                await message.reply(data, mention_author=False)
                return
            else:
                await message.reply("coin not found", mention_author=False)
                return

        # ===== SCHEDULE COMMAND =====
        if "schedule" in text or "reminder" in text or "event" in text:
            now = datetime.now(INDIA_TZ)
            today_name = now.strftime("%A").lower()

            # today
            if "today" in text:
                reminder_text = WEEKLY_REMINDERS.get(today_name, "No schedule")
                await message.reply(reminder_text, mention_author=False)
                return

            # tomorrow
            if "tomorrow" in text:
                tomorrow = now + timedelta(days=1)
                tomorrow_name = tomorrow.strftime("%A").lower()
                reminder_text = WEEKLY_REMINDERS.get(tomorrow_name, "No schedule")
                await message.reply(reminder_text, mention_author=False)
                return

            # specific weekday
            for day in WEEKLY_REMINDERS:
                if day in text:
                    reminder_text = WEEKLY_REMINDERS.get(day, "No schedule")
                    await message.reply(reminder_text, mention_author=False)
                    return

            # default = today
            reminder_text = WEEKLY_REMINDERS.get(today_name, "No schedule")
            await message.reply(reminder_text, mention_author=False)
            return

    await bot.process_commands(message)

bot.run(TOKEN)
