import numpy as np
import requests
import random
from PIL import Image
import sqlite3

from commands.connect import find_user
from games import *

headers = {'Accept': 'application/json'}


async def albumguess(message: discord.Message, lastfmKey: str, client: discord.Client, db: sqlite3.Connection) -> [discord.Message, str, discord.Member | discord.User, [Image], Image, discord.Message]:
    args = message.content.split()[1:]

    if len(args) > 0 and args[0] == "leaderboard":
        await leaderboard(message, client, db)
        return [None, None, None, None, None, None]

    user = find_user(message.author.id)

    if user is None:
        await message.channel.send("You must link your last.fm account to your discord account to view recent charts, run !connect [username].")
        return [None, None, None, None, None, None]

    num = random.randint(1, 500)

    r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user
                     + '&limit=1&page=' + str(num) + '&api_key=' + lastfmKey + '&period=12month' + '&format=json',
                     headers=headers)
    rawjson = r.json()

    if "message" in rawjson and rawjson['message'] == "User not found":
        await message.channel.send("UH OH")
        return [None, None, None, None, None, None]

    try:
        art_link = rawjson['topalbums']['album'][0]['image'][3]['#text']
    except IndexError:
        r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user
                         + '&limit=500&page=1&api_key=' + lastfmKey + '&period=12month' + '&format=json',
                         headers=headers)
        rawjson = r.json()
        length = int(rawjson['topalbums']['@attr']['total'])  # how many total albums they've listened to in past 12months

        num = random.randint(1, length)

        r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user
                         + '&limit=1&page=' + str(num) + '&api_key=' + lastfmKey + '&period=12month' + '&format=json',
                         headers=headers)
        rawjson = r.json()

        if "message" in rawjson and rawjson['message'] == "User not found":
            await message.channel.send("UH OH")
            return [None, None, None, None, None, None]

        art_link = rawjson['topalbums']['album'][0]['image'][3]['#text']

    if art_link == "":
        await message.channel.send("Error: no album art found for this release, please try again.")
        return [None, None, None, None, None, None]

    album_name = rawjson['topalbums']['album'][0]['name']

    hint_name = album_name.split(" ")
    hint_name = [len(word) * "\_" for word in hint_name]
    hint_name = " ".join(hint_name)

    art_content = requests.get(art_link, allow_redirects=True)
    open('art.png', 'wb').write(art_content.content)

    pixeled = pixelate('art.png', 0.02)
    pixeled.save('art_1.png')

    images = []
    images.append(pixelate('art.png', 0.05))
    images.append(pixelate('art.png', 0.12))
    images.append(pixelate('art.png', 0.30))
    final_image = pixelate("art.png", 1)

    sent = await message.channel.send(file=discord.File("art_1.png"))
    hint_message = await message.channel.send(f"{hint_name}")
    await hint_message.add_reaction("😞")
    return [sent, album_name, message.author, images, final_image, hint_message]


async def albumguess_continue(message: discord.Message | None, game: AlbumGuess) -> (bool, bool):
    if check_answer(game, message):
        return True, True

    if len(game.images) == 0:
        return True, False

    image = game.images.pop(0)
    image.save("art_1.png")

    await game.message.edit(attachments=[discord.File("art_1.png")])

    if game.hint_message.content == "":
        hint_text = game.answer.split(" ")
        hint_text = [len(word) * "\_" for word in hint_text]
        hint_text = " ".join(hint_text)

        hint_text = reformat_hint(hint_text, message, game)
    elif message is not None:
        hint_text = reformat_hint(game.hint_message.content, message, game)
    else:
        hint_text = game.hint_message.content

    game.hint_message = await game.hint_message.edit(content=f"{hint_text}")

    return False, None

def reformat_hint(hint_text: str, message: discord.Message, game: AlbumGuess) -> str:
    if message is None:
        return hint_text

    hint_text = hint_text.replace("\_", "_")

    message_split = [word.lower() for word in message.content.split(" ") if word]
    game_split = [word for word in game.answer.split(" ") if word]
    hint_split = [word for word in hint_text.split(" ") if word]

    for i in range(min(len(message_split), len(game_split))):
        for j in range(min(len(game_split[i]), len(message_split[i]))):
            if game_split[i][j].lower() == message_split[i][j]:
                hint_split[i] = hint_split[i][:j] + game_split[i][j] + hint_split[i][j + 1:]

    hint_text = " ".join(hint_split)

    hint_text = hint_text.replace("_", "\_")  # reformat for discord
    return hint_text

async def leaderboard(message: discord.Message, client: discord.Client, db: sqlite3.Connection):
    embed_var = discord.Embed(title="Album Guess Leaderboard", color=0x00ff00)
    #embed_var.add_field(name="",value="MostlikelyHuman - 9999999", inline=False)
    #displayed_users = ""

    cursor = db.cursor()

    db_leaderboard = cursor.execute("SELECT user_id, ag_points, ag_total_games FROM scores WHERE ag_points > 0 ORDER BY ag_points DESC LIMIT 15;")
    #db_leaderboard = cursor.execute("SELECT user_id, ag_points FROM scores ORDER BY ag_points DESC LIMIT 15;")

    value_em = ""
    author_index = 0
    user_count = 1
    for row in db_leaderboard:
        user = await client.fetch_user(int(row[0]))
        user_name = user.display_name
        points = int(row[1])
        total_games = int(row[2])

        if message.author.id == int(row[0]):
            user_points = "**" + str(user_count) + ". " + user_name + " - " + str(points) + " points / " + str(total_games) + " games\n**"
            author_index = user_count
        else:
            user_points = str(user_count) + ". " + user_name + " - **" + str(points) + "** points / **" + str(total_games) + "** games\n"
        value_em += user_points
        user_count += 1

    cursor.close()
    embed_var.add_field(name="", value=value_em, inline=False)

    if author_index != 0:
        embed_var.set_footer(text="You are #" + str(author_index) + "/" + str(user_count-1))

    await message.channel.send(embed=embed_var)

    return


def db_add_game(user_id: int, points: int, db: sqlite3.Connection):
    cursor = db.cursor()

    init_statement = "INSERT or IGNORE INTO scores(user_id, server_id) VALUES (?, 0);"
    cursor.execute(init_statement, (user_id,))

    update_statement = "UPDATE scores SET ag_points = ag_points + ? WHERE user_id = ? AND server_id = 0;"
    cursor.execute(update_statement, (points, user_id))

    update_statement = "UPDATE scores SET ag_total_games = ag_total_games + 1 WHERE user_id = ? AND server_id = 0;"
    cursor.execute(update_statement, (user_id,))

    if points != 0:
        update_statement = "UPDATE scores SET ag_won_games = ag_won_games + 1 WHERE user_id = ? AND server_id = 0;"
        cursor.execute(update_statement, (user_id,))

    db.commit()
    cursor.close()

def pixelate(image_path, pixelation_amount):  # taken from https://medium.com/@charlietapsell1989/python-pixelation-6fc490307a05
    # open image
    im = Image.open(image_path)
    # new dimensions via list comprehension
    new_dims = [int(np.round(a*pixelation_amount)) for a in im.size]
    # downsample, upsample, and return
    return im.resize(new_dims).resize(im.size, resample=4)


def check_answer(game: AlbumGuess, message: discord.Message | None = None):
    # TODO more pre-processing, remove punctuation etc?

    if message is not None and message.content is not None and message.content.lower() == game.answer.lower():
        return True
    else:
        return False