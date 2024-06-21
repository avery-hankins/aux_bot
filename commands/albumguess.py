import numpy as np
import requests
import random
from PIL import Image

from commands.connect import find_user
from games import *

headers = {'Accept': 'application/json'}


async def albumguess(message, lastfmKey) -> [discord.Message, str, discord.Member | discord.User, [Image], Image, discord.Message]:
    args = message.content.split()[1:]

    user = find_user(message.author.id)

    if user is None:
        await message.channel.send("You must link your last.fm account to your discord account to view recent charts, run !connect [username].")
        return [None, None, None, None, None, None]

    num = random.randint(1, 500)

    r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user
                     + '&limit=1&page=' + str(num) + '&api_key=' + lastfmKey + '&period=12month' + '&format=json', headers=headers)
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