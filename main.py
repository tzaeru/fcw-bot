import discord
from discord.ext import commands

import config

bot = commands.Bot(command_prefix = '!')
bot.load_extension('fcw_bot')

@bot.event
async def on_ready():
    print('Logged in as\n '
         f'{bot.user.name}\n '
         f'{bot.user.id}\n '
          '------')

if __name__ == '__main__':
    bot.run(config.bot_token)
