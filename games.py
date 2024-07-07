import discord
import sqlite3

async def stats(message: discord.Message, client: discord.Client, db: sqlite3.Connection):
    cursor = db.cursor()

    cursor.execute("SELECT ag_total_games FROM scores WHERE user_id = ? AND server_id = 0", (message.author.id,))
    ag_total_games = int(cursor.fetchone()[0])
    cursor.execute("SELECT ag_won_games FROM scores WHERE user_id = ? AND server_id = 0", (message.author.id,))
    ag_won_games = int(cursor.fetchone()[0])
    cursor.execute("SELECT ag_points FROM scores WHERE user_id = ? AND server_id = 0", (message.author.id,))
    ag_points = int(cursor.fetchone()[0])

    cursor.close()

    average_points = ag_points / (ag_total_games * 1.0)
    win_rate = (ag_won_games / (ag_total_games * 1.0)) * 100.0

    embed_text = (f"- Total Points: {ag_points}\n- Total Games: {ag_total_games}\n- Average Points/Game: {average_points:.2f}"
                  f"\n- Games Won: {ag_won_games}\n- Win Rate: {win_rate:.1f}%")

    embed_var = discord.Embed(title=f"{message.author.display_name}'s Game Stats", color=0x00ff00)
    embed_var.add_field(name="Album Guess:", value=embed_text, inline=False)

    embed_var.set_thumbnail(url=message.author.display_avatar.url)

    await message.channel.send(embed=embed_var)

class Game:
    def __init__(self, message: discord.message = None, answer: str = None,
                 creator: discord.user = None):
        self.message = message
        self.answer = answer
        self.creator = creator

    def reset(self):
        self.message = None
        self.answer = None
        self.creator = None

    def match(self, message: discord.message = None, user: discord.user = None) -> bool:
        if user is None:
            return message.id == self.message.id
        if message is None:
            return user.id == self.creator.id
        else:
            return message.id == self.message.id and user.id == self.creator.id

    def same_channel(self, message: discord.message) -> bool:
        if self.message is None:
            return False

        return message.channel.id == self.message.channel.id


class Jamble(Game):
    def __init__(self, message, answer, creator):
        super().__init__(message, answer, creator)


class AlbumGuess(Game):
    def __init__(self, message, answer, creator, images, final_image, hint_message):
        super().__init__(message, answer, creator)
        self.images = images
        self.final_image = final_image
        self.end = False
        self.hint_message = hint_message

    def reset(self):
        super().reset()
        self.images = None
        self.final_image = None
        self.end = False
        self.hint_message = None

    def match_hint(self, message: discord.message) -> bool:
        if self.hint_message is None:
            return False

        return message.id == self.hint_message.id
