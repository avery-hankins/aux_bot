import discord
import requests
import io, cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import os
from dotenv import load_dotenv
import user_functions
import traceback

import sys

from collections import defaultdict

#uses rymscraper from https://github.com/dbeley/rymscraper
sys.path.append('../rymscraper-master')

import pandas as pd
from rymscraper import rymscraper, RymUrl

load_dotenv()
token = os.getenv('TOKEN')
lastfmKey = os.getenv('LASTFM')
author = os.getenv('AUTHOR')
art = os.getenv('ART')
gif = os.getenv('GIF')

year = "2024" #assume year is 2024

headers = {'Accept': 'application/json'}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await client.change_presence(activity=discord.Game(name=".help for help!"))

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    if str(message.author.id) == os.getenv("USER1"):
        await message.add_reaction('👎')

    if str(message.author.id) == author:
        await user_functions.function(client, message)

    if message.content.startswith('!battle'):
        args = message.content.split()[1:]

        if len(args) <= 1:
            await message.channel.send("Needs more arguments! Please select a time period or add in more lastfm users.")

        period = args[0] #overall, 7day, 1month, 3month, 6month, 12month
        image = []

        #handle wrong user input
        if period == "alltime" or period == "all" or period == "o" or period == "a":
            period = "overall"
        elif period == "1year" or period == "year" or period == "yearly" or period == "y":
            period = "12month"
        elif period == "month" or period == "monthly" or period == "m":
            period = "1month"
        elif period == "1week" or period == "week" or period == "weekly" or period == "w":
            period = "7day"
        elif period == "quarter" or period == "quarterly" or period == "3m" or period == "q":
            period = "3month"
        elif period == "6m" or period == "h" or period == "half" or period == "halfyear":
            period = "6month"

        if period != "overall" and period != "7day" and period != "1month" and period != "3month" and period != "6month" and period != "12month":
            await message.channel.send("Please select a timeframe for recent plays (7day, 1month, 3month, 6month, 12month, or overall)")
            return

        #50 inputs is max
        if len(args) > 51:
            await message.channel.send("You can not submit more than 50 usernames.")
            return

        work_message = await message.channel.send("Working on it!")

        skipped = []
        less_albums = []

        i = 1
        num_users = len(args)-1

        for user in args[1:]:
            print(user)
            print(str(i) + "/" + str(num_users))
            await work_message.edit(content=f"Working on it! {str(i)}/{str(num_users)}: **{user}**")
            i += 1

            r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.getinfo&user=' + user + '&api_key=' + lastfmKey + '&format=json', headers=headers)
            rawjson = r.json()

            if "message" in rawjson and rawjson['message'] == "User not found":
                skipped.append(user)
                continue

            pfp = rawjson['user']['image'][2]['#text']

            r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user + '&limit=5&period=' + period +'&api_key=' + lastfmKey + '&format=json', headers=headers)

            rawjson = r.json()
            msg = rawjson['topalbums']['album']

            columns = []
            if len(pfp) == 0:
                cv_pfp = cv2.resize(np.array(Image.open("assets/lfmdefault.jpeg")), (174,174))
                cv_pfp = cv2.cvtColor(np.array(cv_pfp), cv2.COLOR_RGB2RGBA)
            else:
                init_pfp = requests.get(pfp)
                bytes_pfp = io.BytesIO(init_pfp.content)
                cv_pfp = cv2.cvtColor(np.array(Image.open(bytes_pfp)), cv2.COLOR_RGB2BGR)
                cv_pfp = cv2.cvtColor(cv_pfp, cv2.COLOR_BGR2RGBA)

            columns.append(cv_pfp)
            columns.append(np.zeros((32, 174, 4), dtype = np.uint8))
            for album in msg:
                if len(album['image'][2]['#text']) > 0:
                    init_im = requests.get(album['image'][2]['#text'])
                    bytes_im = io.BytesIO(init_im.content)
                    cv_im = cv2.cvtColor(np.array(Image.open(bytes_im)), cv2.COLOR_RGB2BGR)
                    cv_im = cv2.cvtColor(cv_im, cv2.COLOR_BGR2RGBA)
                else:
                    blank_album = 255 * np.ones((174, 174, 4), dtype=np.uint8)
                    blank_album = Image.fromarray(blank_album)
                    cv_draw = ImageDraw.Draw(blank_album)

                    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Courier New Bold.ttf", 20)

                    draw_album = album['name']
                    cv_draw.text((0,0), draw_album[:min(13,len(draw_album))], font=font, fill=(255,0,0))
                    if len(draw_album) > 13:
                        if len(draw_album) > 26:
                            draw_album = draw_album[0:23] + "..."
                        cv_draw.text((0,15), draw_album[13:], font=font, fill=(255,0,0))

                    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Courier New.ttf", 20)

                    draw_artist = album['artist']['name']
                    cv_draw.text((0,50), draw_artist[:min(13,len(draw_artist))], font=font, fill=(255,0,0))
                    if len(draw_artist) > 13:
                        if len(draw_artist) > 26:
                            draw_artist = draw_artist[0:23] + "..."
                        cv_draw.text((0,65), draw_artist[13:], font=font, fill=(255,0,0))

                    cv_im = np.array(blank_album)
                    print(cv_im.shape)

                columns.append(cv_im)
                columns.append(np.zeros((16, 174, 4), dtype = np.uint8))

            userColumn = np.vstack(columns)
            if userColumn.shape[0] == 206:
                skipped.append(user)

                continue #skip and continue to next user
            elif userColumn.shape[0] != 1156:
                print("RESIZING")
                less_albums.append(user)

                emptyStack = np.zeros((1156 - userColumn.shape[0], 174, 4), dtype = np.uint8)
                userColumn = np.vstack([userColumn, emptyStack])

            image.append(userColumn)
            image.append(np.zeros((1156, 32, 4), dtype = np.uint8))

        if len(image) == 0:
            await message.channel.send("No valid users!")
            await work_message.delete()
            return

        await work_message.edit(content="Generating image!")
        img = np.hstack(image)

        #crop blank space of image
        img = img[:-16, :-32]

        h, w = img.shape[:2]

        #resize background
        refactor_scale = 1.0
        if img.shape[1] > 1100:
            refactor_scale = img.shape[1] / 1100.0

        h, w = img.shape[:2]
        print(h,w)

        # load background image
        random_bg = random.randint(0, 7)
        back = cv2.cvtColor(np.array(Image.open(f"assets/bg_{str(random_bg)}.jpeg")), cv2.COLOR_RGB2BGR)
        back = cv2.cvtColor(back, cv2.COLOR_BGR2RGBA)
        back = np.array(back)
        hh, ww = back.shape[:2]
        back = cv2.resize(back, (round(ww * refactor_scale), round(hh * refactor_scale)))
        hh, ww = back.shape[:2]
        print(hh,ww)

        # compute xoff and yoff for placement of upper left corner of resized image
        yoff = round((hh-h)/2)
        xoff = round((ww-w)/2)
        print(yoff,xoff)

        # use numpy indexing to place the resized image in the center of background image
        result = back.copy()
        result[round(200*refactor_scale):round(200*refactor_scale)+h, xoff:xoff+w] = img

        #find parts where image is transparent and put background back over them
        mask = result[:, :, 3] == 0
        result[mask] = back[mask]

        #crop bottom of image
        result = result[:round(200*refactor_scale+h+100*refactor_scale)]

        im = Image.fromarray(result[:, :, :3])
        im.save("chart.jpeg")
        await message.channel.send(file=discord.File('chart.jpeg'))

        if len(skipped) != 0:
            error_message = "Skipped: " + str(skipped[0])
            for user in skipped[1:]:
                error_message += ", " + str(user)
            error_message += f" can not be found, or has not listened to any albums in the **{period}** timeframe"
            await message.channel.send(error_message)

        if len(less_albums) != 0:
            error_message = str(less_albums[0])
            for user in less_albums[1:]:
                error_message += ", " + str(user)
            error_message += f" did not listen to five albums in the **{period}** timeframe."
            await message.channel.send(error_message)

        await work_message.delete()

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

    if message.content.startswith('!meeting'):
        args = message.content.split(" ")

        f = open('assets/meetings.txt', 'r')

        if len(args) == 1:
            embedVar = discord.Embed(title=f"Previous Show and Tell Info", color=0x000000)
            line = f.readline()
            inc = 1
            while line:
                line_csv = line.split(",")
                #print(line, end='')
                embedVar.add_field(name=str(inc) + ". " + line_csv[1], value=line_csv[0], inline=False)
                inc += 1
                line = f.readline()
            await message.channel.send(embed=embedVar)
        else:
            if args[1] == 'real':
                line = os.getenv("REAL_STRING")
            else:
                try:
                    query = int(args[1])
                    line = f.read().split("\n")[query - 1]
                except Exception as e:
                    await message.channel.send("Wrong format for command!")
                    f.close()
                    return

            line = line.split(",")
            await message.channel.send("Chart and spotify playlist for " + line[0] + " (" + line[1] + "): " + line[3] + " " + line[2])

        f.close()
        return


    if message.content.startswith('!moneyspread'):
        await message.channel.send(file=discord.File(f"assets/{art}"))
        return

    if message.content.startswith('!rymalbum'):
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

        return


    if message.content.startswith('!rymchart'):
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
        return

    if message.content.startswith('!sbrefresh') and message.author.id == int(author):
        starboard = client.get_channel(int(os.getenv("STARBOARD_CHANNEL")))

        pinned_dict = defaultdict(int)
        stars_dict = defaultdict(int)
        num = 1
        async for sbmessage in starboard.history(limit=9999):
            if sbmessage.author.id != int(os.getenv("STARBOARD_BOT")):
                continue

            embed_index = 0
            for i in range(len(sbmessage.embeds)):
                if len(str(sbmessage.embeds[i].footer)) > len(str(sbmessage.embeds[embed_index].footer)):
                    embed_index = i

            temp_message = str(sbmessage.content)[str(sbmessage.content).index("**")+2:]
            stars = temp_message[0:temp_message.index("**")]
            chan_id = int(str(sbmessage.content)[str(sbmessage.content).index("#")+1:-1])

            message_id = int(str(sbmessage.embeds[embed_index].footer)[str(sbmessage.embeds[embed_index].footer).index(" ")+1:-2])
            try:
                serv = await client.fetch_guild(int(os.getenv("SERVER")))
                chan = await serv.fetch_channel(chan_id)
                sb2message = await chan.fetch_message(message_id)
            except:
                await message.channel.send(str(num) + " Channel not found")
                traceback.print_exc()
                num += 1
                continue

            print(str(num) + " " + sb2message.author.name + " - " + stars)

            sb_author = sb2message.author.name.replace("_", "\_")
            pinned_dict[sb_author] += 1
            stars_dict[sb_author] += int(stars)

            num += 1

        stars_list = sorted(stars_dict.items(), key=lambda key_val: key_val[1], reverse=True)
        pinned_list = sorted(pinned_dict.items(), key=lambda key_val: key_val[1], reverse=True)
        await message.channel.send("DONE")

        f = open("stars.csv", "w")
        for i in range(len(stars_list)):
            f.write(stars_list[i][0]+","+str(stars_list[i][1])+"\n")
        f.close()

        f = open("pinned.csv", "w")
        for i in range(len(pinned_list)):
            f.write(pinned_list[i][0]+","+str(pinned_list[i][1])+"\n")
        f.close()

        return

    if message.content.startswith("!sblb") or message.content.startswith('!starboardleaderboard'):
        stars = True
        if len(message.content.split(" ")) > 1 and message.content.split(" ")[1] == "messages":
            stars = False

        embedVar = discord.Embed(title="Starboard Leaderboard - Most " + str({True: "Stars", False: "Messages Pinned"}[stars]), description="", color=0xFFFF00)

        f = open({True: "stars.csv", False: "pinned.csv"}[stars], "r")
        list_f = f.readlines()
        f.close()

        userCount = 1
        valueEm = ""
        authorIndex = 0
        for pair in list_f[0:15]:
            pair = pair.replace("\n","")
            pair = pair.split(',')

            if message.author.name == pair[0]:
                userStars = "**" + str(userCount) + ". " + pair[0] + " - " + str(pair[1]) + " " + {True: "stars", False: "messages"}[stars] + "\n**"
                authorIndex = userCount
            else:
                userStars = str(userCount) + ". " + pair[0] + " - **" + str(pair[1]) + "** " + {True: "stars", False: "messages"}[stars] + "\n"
            valueEm += userStars
            userCount += 1

        print(valueEm)
        embedVar.set_thumbnail(url="https://images.emojiterra.com/twitter/512px/2b50.png")
        embedVar.add_field(name="",value=valueEm, inline=False)
        if authorIndex != 0:
            embedVar.set_footer(text="You are #" + str(authorIndex) + "/" + str(userCount-1))
        await message.channel.send(embed=embedVar)
        return

client.run(token)