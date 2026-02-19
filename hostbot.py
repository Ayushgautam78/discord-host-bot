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

# ===== RAM REMINDERS (NO FILE = NO CRASH) =====
REMINDERS = []

# ===== WEEKLY SCHEDULE =====
WEEKLY_REMINDERS = {
"monday": "**Super Monday**\n\n**Dawn || n/a ||**\n\n**Sentient || 9:30 PM IST geoguesser ||**",
"tuesday": "**Tuesday**\n\n**Sentient || smashkart 9:30 PM IST ||**",
"wednesday": "**Wednesday**\n\n**Sentient || kirka 9:30 PM IST ||**",
"thursday": "**Thursday**\n\n**Sentient || rebus puzzle 9:30 PM IST ||**",
"friday": "**Friday**\n\n**Sentient || among us 9:30 PM IST ||**",
"saturday": "**No events today. Chill.**",
"sunday": "**No events today. Rest.**"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

morning_active = False
evening_active = False
morning_links = set()
evening_links = set()

# ===== REMINDER LOOP =====
async def reminder_loop():
    await bot.wait_until_ready()
    while True:
        now = datetime.now(INDIA_TZ).strftime("%H:%M")

        for r in REMINDERS[:]:
            if r["time"] == now:
                channel = bot.get_channel(r["channel"])
                if channel:
                    await channel.send(f"<@{r['user']}> Reminder: {r['text']}")
                REMINDERS.remove(r)

        await asyncio.sleep(30)

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

# ===== READY =====
@bot.event
async def on_ready():
    print("Bot online")
    bot.loop.create_task(reminder_loop())

# ===== MESSAGE =====
@bot.event
async def on_message(message):
    global morning_active, evening_active

    if message.author == bot.user:
        return

    # ONLY when bot tagged
    if bot.user in message.mentions:
        text = message.content.lower()

        # remove tag
        for m in message.mentions:
            text = text.replace(f"<@{m.id}>","").replace(f"<@!{m.id}>","")
        text = text.strip()

        now = datetime.now(INDIA_TZ)

        # ===== SET REMINDER =====
        if "remind" in text or "set reminder" in text or "schedule" in text:
            match = re.search(r'(\d{1,2}:\d{2})', text)
            if match:
                time_val = match.group(1)

                reminder_text = text.replace(match.group(1),"")
                reminder_text = reminder_text.replace("remind me","")
                reminder_text = reminder_text.replace("set reminder","")
                reminder_text = reminder_text.replace("schedule","")
                reminder_text = reminder_text.replace("at","").strip()

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

        # ===== PRICE =====
        if "price" in text:
            coin = text.split()[-1]
            data = get_crypto_price(coin)
            if data:
                await message.reply(data, mention_author=False)
            else:
                await message.reply("Coin not found", mention_author=False)
            return

        # ===== TODAY =====
        if "today" in text:
            day = now.strftime("%A").lower()
            await message.reply(WEEKLY_REMINDERS.get(day,"No schedule"), mention_author=False)
            return

    await bot.process_commands(message)

bot.run(TOKEN)
