import os

async def connect(message):
    args = message.content.split(" ")
    if len(args) == 0:
        await message.reply("Please specify a lastfm username.")
        return
    user = args[1]

    user_line = find_user(message.author.id)

    if user_line is not None:
        await message.reply("You have already connected your lastfm account. You're currently not able to switch last.fm usernames.")
        return

    with open("lfm_db.csv", "a") as f:
        f.write(str(message.author.id) + "," + user + "\n")

    await message.channel.send(f"Connected: {user}")


def find_user(user_id: int) -> str | None:
    with open("lfm_db.csv", "r") as f:
        lines = f.readlines()

    lines = [line.split(",") for line in lines]
    user_line = [line for line in lines if line[0] == str(user_id)]

    if len(user_line) == 0:
        return None

    return user_line[0][1]  # lastfm username