import numpy as np
import requests
import random
import discord
from PIL import Image

headers = {'Accept': 'application/json'}

async def albumguess(message, lastfmKey):
    args = message.content.split()[1:]
    if len(args) == 0:
        user = "mostlikelyhuman"
    else:
        user = args[0]

    num = random.randint(1, 500)

    r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user
                     + '&limit=1&page=' + str(num) + '&api_key=' + lastfmKey + '&period=12month' + '&format=json', headers=headers)
    rawjson = r.json()

    if "message" in rawjson and rawjson['message'] == "User not found":
        await message.channel.send("UH OH")
        return [None, None]

    art_link = rawjson['topalbums']['album'][0]['image'][3]['#text']
    art_content = requests.get(art_link, allow_redirects=True)
    open('art.png', 'wb').write(art_content.content)

    pixeled = pixelate('art.png', 0.03)
    pixeled.save('art_1.png')
    pixeled = pixelate('art.png', 0.06)
    pixeled.save('art_2.png')
    pixeled = pixelate('art.png', 0.15)
    pixeled.save('art_3.png')
    pixeled = pixelate('art.png', 0.40)
    pixeled.save('art_4.png')

    await message.channel.send(file=discord.File("art_1.png"))
    await message.channel.send(file=discord.File("art_2.png"))
    await message.channel.send(file=discord.File("art_3.png"))
    await message.channel.send(file=discord.File("art_4.png"))
    await message.channel.send(file=discord.File("art.png"))


def pixelate(image_path, pixelation_amount): # taken from https://medium.com/@charlietapsell1989/python-pixelation-6fc490307a05
    #open image
    im = Image.open(image_path)
    #new dimensions via list comprehension
    new_dims = [int(np.round(a*pixelation_amount)) for a in im.size]
    #downsample, upsample, and return
    return im.resize(new_dims).resize(im.size, resample=4)