#uses rymscraper from https://github.com/dbeley/rymscraper
import sys
sys.path.append('../rymscraper-master')

import discord
import pandas as pd
from rymscraper import rymscraper, RymUrl

import traceback

async def rymchart(message):
    working_message = await message.channel.send("Working on it!")
    network = rymscraper.RymNetwork()

    try:
        args = message.content.split(" ")
        args = args[1:]

        if len(args) == 0:
            year = "2024"
        elif not args[0].isnumeric():
            year = "Alltime"
        else:
            year = args[0]

        if len(args) > 1:
            rym_url = RymUrl.RymUrl(year = year, kind = args[1]) # default: top of all-time.
        else:
            rym_url = RymUrl.RymUrl(year = year) # default: top of all-time.

        chart_infos = network.get_chart_infos(url=rym_url, max_page=1)
        await working_message.edit(content="Generating chart!")
        df = pd.DataFrame(chart_infos)
        if 'Album' not in df:
            await working_message.edit(content="Uh oh! Something went wrong. Please try again with different parameters.")
            return

        df = df[['Album', 'Artist', 'RYM Rating', 'Ratings']]
        df = df.head(min(10, len(df)))

        print(df.iloc[0].iloc[0] + ", " + df.iloc[0].iloc[1])
        top_album_info = network.get_album_infos(name=df.iloc[0].iloc[1] + " - " + df.iloc[0].iloc[0])
        df_top = pd.DataFrame([top_album_info])
        df_top = df_top[['Name', 'Colorscheme', 'Cover']]

        album_color = df_top.iloc[0].iloc[1][0][1:]
        album_color = discord.Color(value=int(album_color, 16))
        print(album_color)
        if len(args) > 1:
            embedVar = discord.Embed(title=f"Best {args[1]}s of {year} - According to RateYourMusic", color=album_color)
        else:
            embedVar = discord.Embed(title=f"Best Albums of {year} - According to RateYourMusic", color=album_color)

        #blocked art
        if df_top.iloc[0].iloc[2] != "https://e.snmc.io/3.0/img/blocked_art/enable_img_600x600.png":
            embedVar.set_thumbnail(url=str(df_top.iloc[0].iloc[2]))

        print(df_top.iloc[0].iloc[2])

        for index, row in df.iterrows():
            embedVar.add_field(name=f"{row.iloc[0]}", value=f"{row.iloc[1]}, {row.iloc[2]}/5.00 from {row.iloc[3]} ratings.", inline=False)
        await message.channel.send(embed=embedVar)
        await working_message.delete()
    except Exception as e:
        await working_message.delete()
        traceback.print_exception(e)
        await message.channel.send("Something went wrong!!")
        await message.channel.send(repr(e))
    finally:
        network.quit()