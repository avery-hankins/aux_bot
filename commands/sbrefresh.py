import traceback
from collections import defaultdict

async def sbrefresh(message, client, starboard_channel, starboard_bot, server):
    starboard = client.get_channel(int(starboard_channel))

    pinned_dict = defaultdict(int)
    stars_dict = defaultdict(int)
    num = 1
    async for sbmessage in starboard.history(limit=9999):
        if sbmessage.author.id != int(starboard_bot):
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
            serv = await client.fetch_guild(server)
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
