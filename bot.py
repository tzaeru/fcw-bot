import random
import urllib, json
import datetime
from datetime import date
from dateutil import parser
import config
import time
import dice
import requests
from tinydb import TinyDB, Query
import random
import discord
import asyncio

def get_games():
    url = "https://freecivweb.org/game/list/json"
    request = requests.get(url=url)
    return request.json()

def sort_games(games):
    sorted = {}
    for game in get_games():
        sorted[game["port"]] = game
    return sorted

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.game_query())
        self.cached_games = sort_games(get_games())

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def game_query(self):
        await self.wait_until_ready()
        channel = self.get_channel(419544412230778880) # channel ID goes here
        while not self.is_closed():
            current_games = get_games()
            for game in current_games:
                if game["port"] in self.cached_games:
                    last_turn = self.cached_games[game["port"]]["turn"]
                    if game["turn"] > last_turn:
                        msg = "Turn changed to " + str(game["turn"]) + " on " + game["message"] + ":" + str(game["port"])
                        print(msg)
                        await channel.send(msg)

            self.cached_games = sort_games(current_games)
            #print(prettified)
            #await channel.send(prettified)
            await asyncio.sleep(10) # task runs every 60 seconds

    async def on_message(self, message):
        if message.content.startswith('!deleteme'):
            msg = await bot.send_message(message.channel, 'I will delete myself now...')
            await bot.delete_message(msg)
            await bot.delete_message(message)

        if message.content.startswith('!'):
            if message.content.startswith('!help'):
                help_msg = "Beep boop!\n\nWork in progress!\n\n"
                await message.channel.send(help_msg)
                return

client = MyClient()
client.run(config.bot_token)