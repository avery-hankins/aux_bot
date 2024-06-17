from PIL import Image, ImageDraw, ImageFont, ImageFilter
import discord
import requests
import commands.chart_utils as chart_utils
from commands.connect import find_user


async def brat(message, lastfmKey):
    args = message.content.split()[1:]

    if len(args) == 0:
        await message.channel.send("Usage: !brat [text], or !brat -chart")
        return

    if args[0] == "-chart" or args[0] == "-c":
        user = find_user(message.author.id)

        if user is None:
            await message.channel.send("You must link your last.fm account to your discord account to view recent charts, run !connect USERNAME.")
            return

        if len(args) > 1:
            period = chart_utils.parseperiod(args[1])
        else:
            period = "7day"

        if len(args) > 2:
            size = chart_utils.parsechartsize(args[2])

            if size[0] * size[1] > 150:
                await message.reply("Erm, what the sigma")
                return
        else:
            size = [3, 3]

        headers = {'Accept': 'application/json'}

        ims = []
        for i in range(1, 1 + size[0] * size[1]):
            r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user
                             + '&limit=1&page=' + str(i) + '&api_key=' + lastfmKey + '&period=' + period + '&format=json', headers=headers)
            rawjson = r.json()

            if "message" in rawjson and rawjson['message'] == "User not found":
                await message.channel.send("UH OH")
                return

            album_name = rawjson['topalbums']['album'][0]['name']
            album_name = album_name.lower()

            ims.append(await bratify(message, album_name))

        w = size[0] * 500
        h = size[1] * 500
        brat_chart = Image.new("RGB", (w, h))

        for i in range(size[0]):
            for j in range(size[1]):
                brat_chart.paste(ims[j * size[0] + i], (i * 500, j * 500))

        brat_chart.save("brat.png", "PNG")

        await message.channel.send(file=discord.File("brat.png"))
    else:
        im = await bratify(message, " ".join(args))
        im.save("brat.png", "PNG")
        await message.channel.send(file=discord.File("brat.png"))


async def bratify(message, text) -> Image:
    print(text)
    W, H = (500,500)

    im = Image.new("RGBA",(W,H),(139, 207, 0, 255))
    draw = ImageDraw.Draw(im)

    w = 401  # placeholder
    h = 401
    font_size = 150
    arial = None

    while w > 350 or h > 350:
        if font_size < 3:
            await message.channel.send("Message too long, can't display properly!")
            return

        arial = ImageFont.truetype("assets/arialnarrow.ttf", font_size)

        lines = ['']
        for word in text.split():
            line = f'{lines[-1]} {word}'.strip()
            print(arial.getbbox(line)[2] - arial.getbbox(line)[0])
            if arial.getbbox(line)[2] - arial.getbbox(line)[0] < 350:  # bbox[2] - [0] is width
                lines[-1] = line
            else:
                lines.append(word)

        text = '\n'.join(lines).strip()

        bbox = draw.multiline_textbbox((0,0), text=text, font=arial, align="center")
        print(bbox)
        w = int(bbox[2])
        h = int(bbox[3])
        print(w, h)

        font_size = int(round(font_size * 0.8))  # shrink font til fits line
        print(f"FONT {font_size}")

    print(w, h)
    print(W, H)
    draw.text(((W-w)/2,(H-h)/2), text, fill="black", font=arial, align="center")

    im = im.filter(ImageFilter.GaussianBlur(radius=2))
    #im.save("brat.png", "PNG")
    #await message.channel.send(file=discord.File("brat.png"))
    return im