#uses rymscraper from https://github.com/dbeley/rymscraper
import sys
sys.path.append('../rymscraper-master')

import discord
import pandas as pd
from rymscraper import rymscraper, RymUrl

async def rymalbum(message):
    working_message = await message.channel.send("Working on it!")
    network = rymscraper.RymNetwork()

    try:
        if message.content.find("-") == -1:
            await working_message.edit(content="Please specify an artist and album name in the format .rymalbum [Artist] - [Album].\nie: .rymalbum The Smiths - The Queen is Dead")
            network.quit()
            return

        album_info = network.get_album_infos(name=message.content[9:])

        print(album_info)

        if album_info == None:
            await working_message.edit(content="Release not found! Please try another search.")
            network.quit()
            return

        df = pd.DataFrame([album_info]).iloc[0]

        hasCover = True
        if 'RYM Rating' not in df:
            await working_message.edit(content="Release exists but has no ratings! Please try another.")
            network.quit()
            return
        if 'Cover' not in df:
            coverdf = pd.Series(["https://e.snmc.io/3.0/img/blocked_art/enable_img_600x600.png"], index = ['Cover'])
            df = pd.concat([df, coverdf])
            df['Colorscheme'] = ['#000000']
        if 'Ranked' in df:
            df = df[['Name', 'Artist', 'RYM Rating', 'Colorscheme', 'Cover', 'Ranked', 'Genres', 'Track listing', 'Type']]
        else:
            df = df[['Name', 'Artist', 'RYM Rating', 'Colorscheme', 'Cover', 'Name', 'Genres', 'Track listing', 'Type']]

        album_color = df.iloc[3][0][1:]
        album_color = discord.Color(value=int(album_color, 16))

        embedVar = discord.Embed(title=f"{df.iloc[0]} [{df.iloc[8]}]", description=f"by {df.iloc[1]}", color=album_color)

        #blocked art
        if df.iloc[4] != "https://e.snmc.io/3.0/img/blocked_art/enable_img_600x600.png":
            embedVar.set_thumbnail(url=str(df.iloc[4]))

        #acts really weird so have to do this
        ratings = df.iloc[2].split("from")
        if df.iloc[0] == df.iloc[5]:
            df.iloc[5] = ""
        embedVar.add_field(name=ratings[0][0:4] + "/5.00, from" + ratings[1], value=df.iloc[5], inline=False)

        embedVar.add_field(name="Genres", value=df.iloc[6], inline=False)

        tracks = ""
        for i in range(len(df.iloc[7])):
            tracks += f"{i+1}. {df.iloc[7][i]}\n"

        if (len(tracks) > 1024):
            tracks = tracks[0:1021] + "..."
        embedVar.add_field(name="Track Listing", value=tracks, inline=False)

        await message.channel.send(embed=embedVar)
        await working_message.delete()
    except Exception as e:
        await working_message.delete()
        traceback.print_exception(e)
        await message.channel.send("Something went wrong!!")
        await message.channel.send(repr(e))
    finally:
        network.quit()
