from PIL import Image, ImageDraw, ImageFont, ImageFilter
import discord

async def bratify(message):
    args = message.content.split()[1:]
    text = " ".join(args)
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

        arial = ImageFont.truetype("Arial Narrow.ttf", font_size)

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
    im.save("brat.png", "PNG")
    await message.channel.send(file=discord.File("brat.png"))