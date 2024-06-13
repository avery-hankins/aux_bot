import requests
import random
import discord
from commands.connect import find_user

headers = {'Accept': 'application/json'}


async def jamble(message, lastfmKey) -> [discord.Message, str, discord.Member | discord.User]:
    args = message.content.split()[1:]

    user = find_user(message.author.id)

    if user is None:
        await message.channel.send("You must link your last.fm account to your discord account to view recent charts, run !connect USERNAME.")
        return [None, None, None]

    num = random.randint(1, 500)

    r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user=' + user
                     + '&limit=1&page=' + str(num) + '&api_key=' + lastfmKey + '&period=12month' + '&format=json', headers=headers)
    rawjson = r.json()

    if "message" in rawjson and rawjson['message'] == "User not found":
        await message.channel.send("UH OH")
        return [None, None, None]

    artist = rawjson['topartists']['artist'][0]['name']
    print(artist)

    artist_upper = artist.upper()

    artist_shuffle = [list(artist) for artist in artist_upper.split(" ")]
    [random.shuffle(word) for word in artist_shuffle]
    artist_shuffle = " ".join(["".join(word) for word in artist_shuffle])

    sent = await message.channel.send("Jamble, 30 seconds to answer: " + artist_shuffle)
    await sent.add_reaction("😞")

    return [sent, artist, message.author]

async def jamble_continue(message, artist) -> bool:
    if message.content.upper() == artist.upper():
        await message.add_reaction("👍")
        await message.channel.send("Jamble: Correct!")
        return True
    else:
        await message.add_reaction("👎")
        return False
