import discord
import os
from dotenv import load_dotenv
import user_functions
import asyncio
import sqlite3

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

from games import *
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

game: dict = dict()  # currently running games

db: sqlite3.Connection = None

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    # Set up database
    # TODO move to new function, better figure out setup?
    global db
    db = sqlite3.connect('database.db')
    cursor = db.cursor()

    sql_statements = [
        """CREATE TABLE IF NOT EXISTS scores (
                user_id INTEGER NOT NULL,
                server_id INTEGER NOT NULL,
                sb_stars INTEGER NOT NULL DEFAULT 0,
                sb_messages INTEGER NOT NULL DEFAULT 0,
                ag_points INTEGER NOT NULL DEFAULT 0,
                ag_won_games INTEGER NOT NULL DEFAULT 0,
                ag_total_games INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, server_id)
        );""",
        """CREATE TABLE IF NOT EXISTS lastfm_users (
                user_id INTEGER NOT NULL PRIMARY KEY,
                lastfm_username TEXT NOT NULL
        );"""]

    #sql_statements = ["CREATE DATABASE IF NOT EXISTS servers;", "SHOW DATABASES"]

    for statement in sql_statements:
        cursor.execute(statement)

    db.commit()
    cursor.close()

    print(f'We have logged in as {client.user}')
    await client.change_presence(activity=discord.Game(name="!help for help"))

@client.event
async def on_message(message):
    global game

    if message.author == client.user:
        return

    if str(message.author.id) == author:
        await user_functions.function(client, message, game)

    if message.author.id in game and game[message.author.id].same_channel(message):
        user_game = game[message.author.id]
        if isinstance(user_game, Jamble):
            done = await jamble_continue(message, client, user_game.answer)
            if done: game.pop(message.author.id)

            return
        if isinstance(user_game, AlbumGuess):
            user_game.end, win = await albumguess_continue(message, user_game)

            if user_game.end:
                user_game.final_image.save("art_1.png")

                points = len(user_game.images) + int(win)
                point_string = "**" + str(points) + "/4 points**"
                await user_game.message.edit(attachments=[discord.File("art_1.png")])

                user_game.hint_message = await user_game.hint_message.edit(content=f"{user_game.answer}")
                if not win:
                    await message.reply(content=f"Incorrect! {point_string}", mention_author=False)
                else:
                    await message.reply(content=f"Album Guess: Correct! {point_string}", mention_author=False)

                db_add_game(message.author.id, points, db)  # TODO fix namespace so it's clear this is ag
                game.pop(message.author.id)

                return
            return



    if message.content.startswith('!album') or message.content.startswith('!albumguess') or message.content.startswith('!ag'):
        game[message.author.id] = AlbumGuess(*(await albumguess(message, lastfmKey, client, db)))

        return

    if message.content.startswith('!battle'):
        await battle(message, lastfmKey)
        return

    if message.content.startswith('!brat'):
        await brat(message, lastfmKey)
        return

    if message.content.startswith('!help'):
        embedVar = discord.Embed(title="Help", description="Commands and description.", color=0x000000)
        embedVar.add_field(name="!ag", value="Album Guess. You'll be given a random blurred album cover, and you have to guess what it is.", inline=False)
        embedVar.add_field(name="!battle", value="Aux battle. Input the timeframe (7day, 1month, 3month, 6month, 12month, overall) and then a list of last.fm usernames. Example: !battle 7day mostlikelyhuman fm-bot", inline=False)
        embedVar.add_field(name="!brat", value="Input text to bratify, or add -chart to get a chart of your recent listening history (but if all the albums were brat).", inline=False)
        embedVar.add_field(name="!connect", value="Connect your last.fm account to your discord account, to use commands that require it.", inline=False)
        embedVar.add_field(name="!donate", value="Donate to support the bot.", inline=False)
        embedVar.add_field(name="!jamble", value="You'll be given a scrambled artist name from your recent listening history, guess who it is!", inline=False)
        embedVar.add_field(name="!help", value="This command.", inline=False)
        embedVar.add_field(name="!meeting", value="View previous PVC meetings, or get chart information about a specific one.", inline=False)
        embedVar.add_field(name="!moneyspread", value="DRANKDRANKDRANKDRANK", inline=False)
        # embedVar.add_field(name="!rymalbum", value="Display some basic information about an album, through RYM's database.", inline=False)  # sonemic no api moment :(
        # embedVar.add_field(name="!rymchart", value="Show the top albums from a given year, according to RYM", inline = False)
        embedVar.add_field(name="!sblb", value="Shows the users with the most Starboard stars (or number of messages pinned with \"!sblb messages)\"", inline=False)
        embedVar.add_field(name="!sbrefresh", value="Refreshes the starboard database, and recalculates the leaderboard.", inline=False)
        await message.channel.send(embed=embedVar)
        return

    if message.content.startswith('!donate'):
        await message.channel.send(f"{gif}")
        return

    if message.content.startswith("!jambmle") or message.content.startswith("!jamble") or message.content.startswith("!j"):
        if message.author.id in game and isinstance(game[message.author.id], Jamble):
            await message.channel.send(f"A game is already in progress. Please wait until it's over.") # TODO multiple games
            return

        game[message.author.id] = Jamble(*(await jamble(message, lastfmKey)))  # pass results of jamble in
        user_game = game[message.author.id]
        if user_game.message is None:
            return

        jamble_message_copy = user_game.message

        await asyncio.sleep(30)

        if message.author.id not in game or user_game.message != jamble_message_copy: # check if game is over already, or new game has been started
            return

        await message.channel.send(f"Time's up! Artist: {user_game.answer}")
        game.pop(message.author.id)

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
        await message.channel.send("Due to changes to the RateYourMusic website, this command is disabled for the foreseeable future.")
        # await rymalbum(message)
        return

    if message.content.startswith('!rymchart'):
        await message.channel.send("Due to changes to the RateYourMusic website, this command is disabled for the foreseeable future.")
        # await rymchart(message)
        return

    if message.content.startswith('!sbrefresh') and message.author.id == int(author):
        await sbrefresh(message, client, starboard_bot, threshold)
        return

    if message.content.startswith("!sblb") or message.content.startswith('!sbleaderboard') or message.content.startswith('!starboardleaderboard'):
        await sbleaderboard(message, client, starboard_bot, threshold)
        return

    if message.content.startswith("!stats"):
        await stats(message, client, db)
        return


@client.event
async def on_reaction_add(reaction, user):
    global game
    message = reaction.message
    if user.id in game:
        user_game = game[user.id]
        if isinstance(user_game, Jamble) and user_game.match(message, user):
            if reaction.emoji == "😞":
                await message.channel.send(f"{user.mention} gave up.")
                await message.channel.send(f"Artist: {user_game.answer}")
                game.pop(user.id)
                return
        if isinstance(user_game, AlbumGuess) and user_game.match(user=user):
            if reaction.emoji != "😞":
                return  # early return

            user_game.final_image.save("art_1.png")

            points = "**0/4 points**"
            await user_game.message.edit(attachments=[discord.File("art_1.png")])

            await message.channel.send(f"{user.mention} gave up. {points}")
            user_game.hint_message = await user_game.hint_message.edit(content=f"{user_game.answer}")
            db_add_game(user.id, 0, db)
            game.pop(user.id)
            return

@client.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    message = after

    if message.author.id in game and game[message.author.id].same_channel(message):
        user_game = game[message.author.id]
        if isinstance(user_game, Jamble):
            done = await jamble_continue(message, client, user_game.answer)
            if done: game.pop(message.author.id)

            return
        if isinstance(user_game, AlbumGuess):
            user_game.end, win = await albumguess_continue(message, user_game)

            if user_game.end:
                user_game.final_image.save("art_1.png")

                points = len(user_game.images) + int(win)
                point_string = "**" + str(points) + "/4 points**"
                await user_game.message.edit(attachments=[discord.File("art_1.png")])

                user_game.hint_message = await user_game.hint_message.edit(content=f"{user_game.answer}")
                if not win:
                    await message.reply(content=f"Incorrect! {point_string}", mention_author=False)
                else:
                    await message.reply(content=f"Album Guess: Correct! {point_string}", mention_author=False)

                db_add_game(message.author.id, points, db)  # TODO fix namespace so it's clear this is ag
                game.pop(message.author.id)

                return
            return


client.run(token)