import traceback
from collections import defaultdict

async def sbrefresh(message, client, starboard_bot, threshold):
    server_id = message.channel.guild.id

    if len(message.content.split(" ")) == 2:
        starboard_channel = message.content.split(" ")[1]
    else:
        try:
            f = open(str(server_id) + "_stars.csv", "r")
            starboard_channel = f.readlines()[0].replace("\n","")
            f.close()
        except:
            await message.channel.send("No database found, please input the id of your starboard channel as !sbrefresh 123....")
            return
    
    starboard = client.get_channel(int(starboard_channel))

    pinned_dict = defaultdict(int)
    stars_dict = defaultdict(int)

    #remove posts with less than the 7 threshold
    pinned_cut_dict = defaultdict(int)
    stars_cut_dict = defaultdict(int)

    num = 1

    most_recent_message = -1
    await message.channel.send("Refreshing! 🌴😎🍹")
    async for sbmessage in starboard.history(limit=9999):
        if sbmessage.author.id != int(starboard_bot):
            continue

        if most_recent_message == -1:
            most_recent_message = sbmessage.id

        embed_index = 0
        for i in range(len(sbmessage.embeds)):
            if len(str(sbmessage.embeds[i].footer)) > len(str(sbmessage.embeds[embed_index].footer)):
                embed_index = i

        temp_message = str(sbmessage.content)[str(sbmessage.content).index("**")+2:]
        stars = temp_message[0:temp_message.index("**")]
        if str(sbmessage.content).find("#") != -1:
            #old sb system
            chan_id = int(str(sbmessage.content)[str(sbmessage.content).index("#")+1:-1])
            message_id = int(str(sbmessage.embeds[embed_index].footer)[str(sbmessage.embeds[embed_index].footer).index(" ")+1:-2])
        else:
            #new sb system
            args = str(sbmessage.content)[str(sbmessage.content).index("discord.com"):]
            args = args.split("/")
            chan_id = int(args[3])
            message_id = int(args[4])

        try:
            serv = message.channel.guild
            chan = await serv.fetch_channel(chan_id)
            sb2message = await chan.fetch_message(message_id)
        except:
            #await message.channel.send(str(num) + " Channel not found")
            traceback.print_exc()
            num += 1
            continue

        print(str(num) + " " + sb2message.author.name + " - " + stars)

        sb_author = sb2message.author.name.replace("_", "\_")
        pinned_dict[sb_author] += 1
        stars_dict[sb_author] += int(stars)
        pinned_cut_dict[sb_author] += 1
        stars_cut_dict[sb_author] += int(stars)

        #offset
        if int(stars) < 7:
            pinned_cut_dict[sb_author] -= 1
            stars_cut_dict[sb_author] -= int(stars)

        num += 1

    stars_list = sorted(stars_dict.items(), key=lambda key_val: key_val[1], reverse=True)
    pinned_list = sorted(pinned_dict.items(), key=lambda key_val: key_val[1], reverse=True)
    stars_cut_list = sorted(stars_cut_dict.items(), key=lambda key_val: key_val[1], reverse=True)
    pinned_cut_list = sorted(pinned_cut_dict.items(), key=lambda key_val: key_val[1], reverse=True)


    f = open(str(server_id) + "_stars.csv", "w")
    f.write(starboard_channel + "\n")
    f.write(str(most_recent_message) + "\n")
    for i in range(len(stars_list)):
        f.write(stars_list[i][0]+","+str(stars_list[i][1])+"\n")
    f.close()

    f = open(str(server_id) + "_pinned.csv", "w")
    f.write(starboard_channel + "\n")
    f.write(str(most_recent_message) + "\n")
    for i in range(len(pinned_list)):
        f.write(pinned_list[i][0]+","+str(pinned_list[i][1])+"\n")
    f.close()

    f = open(str(server_id) + "_stars_cut.csv", "w")
    f.write(starboard_channel + "\n")
    f.write(str(most_recent_message) + "\n")
    for i in range(len(stars_cut_list)):
        f.write(stars_cut_list[i][0]+","+str(stars_cut_list[i][1])+"\n")
    f.close()

    f = open(str(server_id) + "_pinned_cut.csv", "w")
    f.write(starboard_channel + "\n")
    f.write(str(most_recent_message) + "\n")
    for i in range(len(pinned_cut_list)):
        f.write(pinned_cut_list[i][0]+","+str(pinned_cut_list[i][1])+"\n")
    f.close()

    await message.channel.send("Lists refreshed!")

async def recent_id(message):
    server_id = message.channel.guild.id

    f = open(str(server_id) + "_stars.csv", "r")
    starboard_channel = f.readlines()[0].replace("\n","")
    f.close()

    starboard = await message.channel.guild.fetch_channel(int(starboard_channel))
    async for sbmessage in starboard.history(limit=1):
        return sbmessage.id
