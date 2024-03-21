import discord

async def meeting(message, real_string):
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
            line = real_string
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