import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
import random
import discord
import io
import commands.chart_utils as chart_utils

headers = {'Accept': 'application/json'}

async def battle(message, lastfmKey):
    args = message.content.split()[1:]

    if len(args) <= 1:
        await message.channel.send("Needs more arguments! Please select a time period or add in more lastfm users.")

    period = args[0] #overall, 7day, 1month, 3month, 6month, 12month
    image = []

    #handle wrong user input
    period = chart_utils.parseperiod(period)

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
            cv_pfp = Image.open("assets/lfmdefault.jpeg")
            cv_pfp = cv_pfp.resize((174,174), Image.Resampling.LANCZOS)
            cv_pfp = cv_pfp.convert("RGBA")
        else:
            init_pfp = requests.get(pfp)
            bytes_pfp = io.BytesIO(init_pfp.content)
            cv_pfp = Image.open(bytes_pfp)
            cv_pfp = cv_pfp.convert("RGBA")

        columns.append(cv_pfp)
        columns.append(np.zeros((32, 174, 4), dtype = np.uint8))
        for album in msg:
            if len(album['image'][2]['#text']) > 0:
                init_im = requests.get(album['image'][2]['#text'])
                bytes_im = io.BytesIO(init_im.content)
                cv_im = Image.open(bytes_im)
                cv_im = cv_im.convert("RGBA")
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
    back_small = Image.open(f"assets/bg_{str(random_bg)}.jpeg")
    width = back_small.size[0]
    final_height = round(300+h/refactor_scale)
    back_small = back_small.crop((0, 0, width, final_height))
    back_small = back_small.convert("RGBA")
    hh, ww = np.asarray(back_small).shape[:2]

    back = back_small.resize((round(ww * refactor_scale), round(hh * refactor_scale)))
    del back_small # freeing memory
    hh = round(hh * refactor_scale)
    ww = round(ww * refactor_scale)
    print(hh,ww)

    # compute xoff and yoff for placement of upper left corner of resized image
    yoff = round((hh-h)/2)
    xoff = round((ww-w)/2)
    print(yoff,xoff)

    # use numpy indexing to place the resized image in the center of background image
    back_array = np.array(back)
    del back
    # generate mask of non-transparent image, and overlay it over background
    mask = img[:, :, 3] != 0
    img_mask = img[mask]
    del img

    back_array[round(200*refactor_scale):round(200*refactor_scale)+h, xoff:xoff+w][mask] = img_mask
    del mask
    del img_mask

    im = Image.fromarray(back_array[:, :, :3])
    del back_array
    im.save("chart.jpeg")
    del im

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