import asyncio
import discord
from discord.ext import commands, tasks
from tinydb import TinyDB, Query

import config
import fcw_web_utils

games_db = TinyDB('games_db.json')

# Role IDs from the freecivweb server that are permitted to use the bot.
allowed_roles = (
    466569078140698624,
    663815632667803648,
    428834617810878466,
    466898941485776905)
    
class FcwBot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.cached_games = fcw_web_utils.get_game_list()
        # Queue task to query game list.
        self.task_update_cache = \
            asyncio.get_event_loop().create_task(self.game_query())

    async def game_query(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(666394570430611476)
        while not self.bot.is_closed():
            current_games = fcw_web_utils.get_game_list()
            # Iterate through each running game, and check whether the turn
            # has changed. If so, send a message.
            for port, game in current_games.items():
                if port in self.cached_games:
                    last_turn = self.cached_games[port]['turn']
                    if game['turn'] > last_turn:
                        msg = f'Turn changed to {game["turn"]} on ' \
                              f'{game["message"]}:{port}'
                        print(msg)
                        await channel.send(msg)

            self.cached_games = current_games
            await asyncio.sleep(60) # Task runs every 60 seconds.

    # Load a game from the DB or return None.
    def get_game(self, game_name):
        query = Query()
        games = games_db.search(query.name == game_name)
        game = None
        if len(games) > 0:
            game = games[0]
        return game

    @commands.command(help='Creates a new game.')
    @commands.has_any_role(*allowed_roles)
    async def create(self, ctx, *, game_name):
        # Look for a game information category.
        game_category = None
        for category in ctx.guild.categories:
            if category.name == 'Game Information':
                game_category = category
                break
        if game_category is None:
            await ctx.send('No channel category \'Game Information\'.')
            return

        # Make sure a channel and role for the game do not yet exist.
        channels = ctx.guild.channels
        if any(channel.name == game_name for channel in channels):
            await message.channel.send('Error: Existing channel with that ' \
                                       'name found.')
            return

        roles = ctx.guild.roles
        if any(role.name == game_name for role in roles):
            await message.channel.send('Error: Existing role with that ' \
                                       'name found.')

        # End of checks, get the attached LT file.
        if len(ctx.message.attachments) == 0:
            await ctx.send('You must attach a game link.')
            return
        game_file = ctx.message.attachments[0]
        file_path = config.publite2_path + game_file.filename

        # Validate filename.
        if not game_file.filename[-5:] == '.serv':
            await ctx.send('Error: Extension for server configs needs to be '
                           '.serv.')
            return
        if not game_file.filename.startswith('LT_'):
            await ctx.send('Error: .serv files need to start with LT_.')
            return

        # Prevent overwriting existing file.
        if not path.exists(file_path):
            await game_file.save(file_path)
        else:
            await ctx.send('Error: Server file with the same name already '
                           ' exists')
            return

        # Create channel and role for the game.
        channel = await ctx.guild.create_text_channel(game_name,
            category=game_category)
        role = await ctx.guild.create_role(name=game_name)
        games_db.insert({
                'name' : game_name,
                'channel-id' : channel.id,
                'role-id' : role.id,
            })

        # Send the id of the new role back.
        await ctx.send(role.id)

    @commands.command(help='Deletes a game.')
    @commands.has_any_role(*allowed_roles)
    async def delete(self, ctx, *, game_name):   
        game = self.get_game(game_name)
        if game is None:
            await ctx.send('Game not found.')
            return

        # Remove role and channel.
        role = ctx.guild.get_role(game['role-id'])
        if role:
            await role.delete()

        channel = ctx.guild.get_channel(game['channel-id'])
        if channel:
            await channel.delete()

        # Remove game from the DB.
        query = Query()
        games_db.remove(query.name == game_name)
        await ctx.send(game)

    @commands.command(help='Adds you to a game.')
    async def join(self, ctx, *, game_name):
        game = self.get_game(game_name)
        if game is None:
            await ctx.send('Game not found.')
            return

        role = ctx.guild.get_role(game['role-id'])
        await ctx.author.add_roles(role)
        await ctx.send(f'You\'ve been added to {game_name}!')

    @commands.command(help='Removes you from a game.')
    async def leave(self, ctx, *, game_name):
        game = self.get_game(game_name)
        if game is None:
            await ctx.send('Game not found.')
            return

        role = ctx.guild.get_role(game['role-id'])
        await ctx.author.remove_roles(role)
        await ctx.send(f'You\'ve been removed from {game_name}.')

def setup(bot):
    bot.add_cog(FcwBot(bot))
