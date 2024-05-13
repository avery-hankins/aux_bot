import discord
from commands.sbrefresh import sbrefresh, recent_id

async def sbleaderboard(message, client, starboard_bot, threshold):
    stars = True
    grandfathered = True
    if len(message.content.split(" ")) > 1 and message.content.split(" ")[1] == "messages":
        stars = False

    for arg in message.content.split(" "):
        if arg == "-grandfathered=False":
            grandfathered = False


    embedVar = discord.Embed(title="Starboard Leaderboard - Most " + str({True: "Stars", False: "Messages Pinned"}[stars]), description="", color=0xFFFF00)

    server_id = message.channel.guild.id
    try:
        file = {True: (str(server_id) + "_stars"), False: (str(server_id) + "_pinned")}[stars]
        file += {True: (".csv"), False: ("_cut.csv")}[grandfathered]

        f = open(file, "r")
        list_f = f.readlines()
        f.close()
    except:
        db_message = await message.channel.send("Database doesn't exist! Running !sbrefresh command...")
        await sbrefresh(message, client, starboard_bot, threshold)
        file = {True: (str(server_id) + "_stars"), False: (str(server_id) + "_pinned")}[stars]
        file += {True: (".csv"), False: ("_cut.csv")}[grandfathered]

        f = open(file, "r")
        list_f = f.readlines()
        f.close()
        await db_message.delete()

    recent_id_val = await recent_id(message)
    if int(list_f[1]) != int(recent_id_val):
        db_message = await message.channel.send("Database needs to update! Running !sbrefresh command...")
        await sbrefresh(message, client, starboard_bot, threshold)
        await sbleaderboard(message, client, starboard_bot, threshold)
        await db_message.delete()
        return

    userCount = 1
    valueEm = ""
    authorIndex = 0
    for pair in list_f[2:17]:
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

    if not grandfathered:
        await message.channel.send(content="Displaying results when counting all posts over the current star threshold.")

    embedVar.set_thumbnail(url="https://images.emojiterra.com/twitter/512px/2b50.png")
    embedVar.add_field(name="",value=valueEm, inline=False)
    if authorIndex != 0:
        embedVar.set_footer(text="You are #" + str(authorIndex) + "/" + str(userCount-1))
    await message.channel.send(embed=embedVar)