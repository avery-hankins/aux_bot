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

from commands.battle import battle
from commands.brat import bratify
from commands.jamble import *
from commands.meeting import meeting
from commands.rymalbum import rymalbum
from commands.rymchart import rymchart
from commands.sbrefresh import sbrefresh
from commands.sbleaderboard import sbleaderboard

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

jamble_state = None
jamble_artist = None
jamble_user = None

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await client.change_presence(activity=discord.Game(name="!help for help"))

@client.event
async def on_message(message):
    global jamble_state, jamble_artist, jamble_user

    if message.author == client.user:
        return

    if str(message.author.id) == author:
        await user_functions.function(client, message)

    if jamble_state is not None and message.channel.id == jamble_state.channel.id:
        done = await jamble_continue(message, jamble_artist)

        if done:
            jamble_state = None
            jamble_artist = None
            jamble_user = None

        return

    if message.content.startswith('!battle'):
        await battle(message, lastfmKey)
        return

    if message.content.startswith('!brat'):
        await bratify(message)
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
        [jamble_state, jamble_artist, jamble_user] = await jamble(message, lastfmKey)
        jamble_state_copy = jamble_state

        await asyncio.sleep(30)

        if jamble_state != jamble_state_copy: # check if game is over already, or new game has been started
            return

        await message.channel.send(f"Time's up! Artist: {jamble_artist}")

        jamble_state = None
        jamble_artist = None
        jamble_user = None

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
    global jamble_state, jamble_artist, jamble_user
    message = reaction.message
    if jamble_state is not None and message.id == jamble_state.id and user.id == jamble_user.id:
        if reaction.emoji == "😞":
            await message.channel.send(f"Loser {user.mention} gave up.")
            await message.channel.send(f"Artist: {jamble_artist}")
            jamble_state = None
            jamble_artist = None
            jamble_user = None
            return

client.run(token)