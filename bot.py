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
import urllib.request
from os import path

games_db = TinyDB('games_db.json')

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
                        #await channel.send(msg)

            self.cached_games = sort_games(current_games)
            #print(prettified)
            #await channel.send(prettified)
            await asyncio.sleep(10) # task runs every 60 seconds

    async def on_message(self, message):

        # We check for specific roles on the message author before allowing
        # any of the admin-like commands below. The IDs are magic to roles
        # of Freeciv-web Discord.
        for role in message.author.roles:
            if (role.id == 466569078140698624
                or role.id == 663815632667803648
                or role.id == 428834617810878466
                or role.id == 466898941485776905):
                break
        else:
            return

        if message.content.startswith('!deleteme'):
            msg = await bot.send_message(message.channel, 'I will delete myself now...')
            await bot.delete_message(msg)
            await bot.delete_message(message)

        if message.content.startswith('!'):
            if message.content.startswith('!help'):
                help_msg = "Beep boop!\n\nWork in progress!\n\n"
                await message.channel.send(help_msg)
                return

            if message.content.startswith('!create'):
                game_name = message.content[message.content.find(' ')+1:]
                if len(game_name) > 0:
                    categories = message.guild.categories
                    game_category = None
                    for category in categories:
                        if category.name == "Game Information":
                            game_category = category
                            break
                    if category == None:
                        return

                    # Make sure no such channel and role exist yet
                    channels = message.guild.channels
                    print(channels)
                    if any(channel.name == game_name for channel in channels):
                        await message.channel.send("Error: Existing channel with that name found.")
                        return
                    roles = message.guild.roles
                    if any(role.name == game_name for role in roles):
                        await message.channel.send("Error: Existing role with that name found.")
                        return

                    # All checks complete, proceed!
                    # Get the attached LT file
                    filename = message.attachments[0].filename
                    file_path = config.publite2_path + filename
                    if filename.split(".")[-1] != "serv":
                        await message.channel.send("Error: Extension for serer configs needs to be .serv.")
                        return
                    if not filename.startswith("LT_"):
                        await message.channel.send("Error: .serv files need to start with LT_.")
                        return
                    if not path.exists(file_path):
                        await message.attachments[0].save(file_path)
                    else:
                        await message.channel.send("Error: Server file with the same name already exists.")
                        return

                    channel = await message.guild.create_text_channel(game_name, category=game_category)
                    role = await message.guild.create_role(name=game_name)
                    games_db.insert({'name': game_name, 'channel-id': channel.id, 'role-id': role.id})
                    await message.channel.send(role.id)
                return

            if message.content.startswith('!delete'):
                game_name = message.content[message.content.find(' ')+1:]
                if len(game_name) > 0:

                    query = Query()
                    games = games_db.search(query.name == game_name)
                    game = None

                    if len(games) > 0:
                        game = games[0]
                    else:
                        await message.channel.send("Game not found.")
                        return

                    role = message.guild.get_role(game["role-id"])
                    if role:
                        await role.delete()

                    channel = message.guild.get_channel(game["channel-id"])
                    if channel:
                        await channel.delete()
                    games_db.remove(query.name == game_name)

                    await message.channel.send(game)
                return

            if message.content.startswith('!join') or message.content.startswith('!leave'):
                game_name = message.content[message.content.find(' ')+1:]
                if len(game_name) > 0:

                    query = Query()
                    games = games_db.search(query.name == game_name)
                    game = None
                    if len(games) > 0:
                        game = games[0]
                    else:
                        await message.channel.send("Game not found.")
                        return

                    role = message.guild.get_role(game["role-id"])

                    if message.content.startswith('!join'):
                        await message.author.add_roles(role)
                        await message.channel.send("You've been added to " + game_name)
                    else:
                        await message.author.remove_roles(role)
                        await message.channel.send("You've been removed from " + game_name)
                return

client = MyClient()
client.run(config.bot_token)