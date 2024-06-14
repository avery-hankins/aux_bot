import numpy as np
import requests
import random
from PIL import Image

from commands.connect import find_user
from games import *

headers = {'Accept': 'application/json'}


async def albumguess(message, lastfmKey) -> [discord.Message, str, discord.Member | discord.User, [Image], Image]:
    args = message.content.split()[1:]

    user = find_user(message.author.id)

    if user is None:
        await message.channel.send("You must link your last.fm account to your discord account to view recent charts, run !connect USERNAME.")
        return [None, None, None, None]

    num = random.randint(1, 500)

    r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user
                     + '&limit=1&page=' + str(num) + '&api_key=' + lastfmKey + '&period=12month' + '&format=json', headers=headers)
    rawjson = r.json()

    if "message" in rawjson and rawjson['message'] == "User not found":
        await message.channel.send("UH OH")
        return [None, None, None, None]

    art_link = rawjson['topalbums']['album'][0]['image'][3]['#text']
    album_name = rawjson['topalbums']['album'][0]['name']

    hint_name = album_name.split(" ")
    hint_name = [len(word) * "\_" for word in hint_name]
    hint_name = " ".join(hint_name)

    art_content = requests.get(art_link, allow_redirects=True)
    open('art.png', 'wb').write(art_content.content)

    pixeled = pixelate('art.png', 0.03)
    pixeled.save('art_1.png')

    images = []
    images.append(pixelate('art.png', 0.06))
    images.append(pixelate('art.png', 0.15))
    images.append(pixelate('art.png', 0.40))
    final_image = pixelate("art.png", 1)

    sent = await message.channel.send(file=discord.File("art_1.png"))
    await message.channel.send(f"Hint: {hint_name}")
    return [sent, album_name, message.author, images, final_image]
    # await message.channel.send(file=discord.File("art_2.png"))
    # await message.channel.send(file=discord.File("art_3.png"))
    # await message.channel.send(file=discord.File("art_4.png"))
    # await message.channel.send(file=discord.File("art.png"))


async def albumguess_continue(message: discord.Message, game: AlbumGuess) -> bool:
    if message.content.lower() == game.answer.lower():
        await message.channel.send("Album Guess: Correct!")
        await message.add_reaction("👍")
        return True

    image = game.images.pop(0)
    image.save("art_1.png")

    await message.channel.send(file=discord.File("art_1.png"))
    return False


def pixelate(image_path, pixelation_amount):  # taken from https://medium.com/@charlietapsell1989/python-pixelation-6fc490307a05
    #open image
    im = Image.open(image_path)
    #new dimensions via list comprehension
    new_dims = [int(np.round(a*pixelation_amount)) for a in im.size]
    #downsample, upsample, and return
    return im.resize(new_dims).resize(im.size, resample=4)