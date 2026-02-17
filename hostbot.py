import discord
from discord.ext import commands
import requests

import os
TOKEN = os.getenv("TOKEN")


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

@bot.event
async def on_ready():
    print("Hosting bot online")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        text = message.content.lower()

        if "price" in text or "fdv" in text:
            coin = text.split()[-1]
            data = get_crypto_price(coin)

            if data:
                await message.reply(data, mention_author=False)
            else:
                await message.reply("coin not found", mention_author=False)

    await bot.process_commands(message)

bot.run(TOKEN)
