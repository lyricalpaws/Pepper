import discord
import json
import os
import asyncio
from datetime import datetime
from discord.ext import commands
from discord import Intents

# Get config.json
with open("config.json", "r") as config:
    data = json.load(config)
    prefix = data["prefix"]

bot = commands.Bot(prefix, intents=Intents.all())


@bot.event
async def on_ready():
    if not hasattr(bot, "uptime"):
        bot.uptime = datetime.utcnow()
    print(f"We have logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{bot.command_prefix}help"))
    print(discord.__version__)


async def main():
    async with bot:
        bot.remove_command("help")
        try:
            print("Logging in...")
            for file in os.listdir("cogs"):
                if file.endswith(".py"):
                    name = file[:-3]
                    await bot.load_extension(f"cogs.{name}")
            await bot.start(data['token'])
        except KeyboardInterrupt:
            bot.close()

asyncio.run(main())
