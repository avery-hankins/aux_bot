import discord

async def sbleaderboard(message):
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