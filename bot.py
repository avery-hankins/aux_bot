import discord
import os
from dotenv import load_dotenv
import user_functions
import asyncio

load_dotenv()
token = os.getenv('TOKEN')
lastfmKey = os.getenv('LASTFM')
author = os.getenv('AUTHOR')
art = os.getenv('ART')
gif = os.getenv('GIF')
real_string = os.getenv('REAL_STRING')

#starboard_channel = os.getenv('STARBOARD_CHANNEL')
starboard_bot = os.getenv('STARBOARD_BOT')
#server = os.getenv('SERVER')
threshold = os.getenv('STAR_THRESHOLD')

year = "2024" #assume year is 2024

from commands.albumguess import *
from commands.battle import battle
from commands.brat import *
from commands.connect import connect
from commands.jamble import *
from commands.meeting import meeting
from commands.rymalbum import rymalbum
from commands.rymchart import rymchart
from commands.sbrefresh import sbrefresh
from commands.sbleaderboard import sbleaderboard

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

game_message = None
game_answer = None
game_creator = None
game_type = None # should be "albumguess" or "jamble", etc
game_stage = 0

client = discord.Client(intents=intents)

def reset_game():
    global game_message, game_answer, game_creator, game_type, game_stage
    game_message = None
    game_answer = None
    game_creator = None
    game_type = None
    game_stage = 0

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await client.change_presence(activity=discord.Game(name="!help for help"))

@client.event
async def on_message(message):
    global game_message, game_answer, game_creator, game_type, game_stage

    if message.author == client.user:
        return

    if str(message.author.id) == author:
        await user_functions.function(client, message)

    if game_type == "jamble" and message.channel.id == game_message.channel.id:
        done = await jamble_continue(message, game_answer)
        if done: reset_game()

        return

    if game_type == "albumguess" and message.channel.id == game_message.channel.id:
        game_stage = await albumguess_continue(message, game_answer)
        if done: reset_game()

        return

    if message.content.startswith('!album') or message.content.startswith('!albumguess') or message.content.startswith('!ag'):
        await albumguess(message, lastfmKey)
        return

    if message.content.startswith('!battle'):
        await battle(message, lastfmKey)
        return

    if message.content.startswith('!brat'):
        await brat(message, lastfmKey)
        return

    if message.content.startswith('!help'):
        embedVar = discord.Embed(title="Help", description="Commands and description.", color=0x000000)
        embedVar.add_field(name="!battle", value="Aux battle. Input the timeframe (7day, 1month, 3month, 6month, 12month, overall) and then a list of last.fm usernames. Example: !battle 7day mostlikelyhuman fm-bot", inline=False)
        embedVar.add_field(name="!donate", value="Donate to support the bot.", inline=False)
        embedVar.add_field(name="!help", value="This command.", inline=False)
        embedVar.add_field(name="!meeting", value="View previous meetings, or get chart information about a specific one.", inline=False)
        embedVar.add_field(name="!moneyspread", value="DRANKDRANKDRANKDRANK", inline=False)
        embedVar.add_field(name="!rymalbum", value="Display some basic information about an album, through RYM's database.", inline=False)
        embedVar.add_field(name="!rymchart", value="Show the top albums from a given year, according to RYM", inline = False)
        embedVar.add_field(name="!sblb", value="Shows the users with the most Starboard stars (or number of messages pinned with \"!sblb messages)\"", inline=False)
        await message.channel.send(embed=embedVar)
        return

    if message.content.startswith('!donate'):
        await message.channel.send(f"{gif}")
        return

    if message.content.startswith("!jambmle") or message.content.startswith("!jamble") or message.content.startswith("!j"):
        if game_type == "jamble":
            await message.channel.send(f"A game is already in progress. Please wait until it's over.") # TODO multiple games
            return

        [game_message, game_answer, game_creator] = await jamble(message, lastfmKey)
        if game_message is None:
            return
        
        game_type = "jamble"
        jamble_state_copy = game_message

        await asyncio.sleep(30)

        if game_message != jamble_state_copy: # check if game is over already, or new game has been started
            return

        await message.channel.send(f"Time's up! Artist: {game_answer}")
        reset_game()

        return

    if message.content.startswith('!connect'):
        await connect(message)
        return

    if message.content.startswith('!meeting'):
        await meeting(message, real_string)
        return

    if message.content.startswith('!moneyspread'):
        await message.channel.send(file=discord.File(f"assets/{art}"))
        return

    if message.content.startswith('!rymalbum'):
        await rymalbum(message)
        return

    if message.content.startswith('!rymchart'):
        await rymchart(message)
        return

    if message.content.startswith('!sbrefresh') and message.author.id == int(author):
        await sbrefresh(message, client, starboard_bot, threshold)
        return

    if message.content.startswith("!sblb") or message.content.startswith('!sbleaderboard') or message.content.startswith('!starboardleaderboard'):
        await sbleaderboard(message, client, starboard_bot, threshold)
        return


@client.event
async def on_reaction_add(reaction, user):
    global game_message, game_answer, game_creator
    message = reaction.message
    if game_message is not None and message.id == game_message.id and user.id == game_creator.id:
        if reaction.emoji == "😞":
            await message.channel.send(f"Loser {user.mention} gave up.")
            await message.channel.send(f"Artist: {game_answer}")
            reset_game()
            return

client.run(token)