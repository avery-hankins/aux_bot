import discord


class Game:
    def __init__(self, message: discord.message = None, answer: str = None,
                 creator: discord.user = None, type: str = None):
        self.message = message
        self.answer = answer
        self.creator = creator
        self.type = type

    def reset(self):
        self.message = None
        self.answer = None
        self.creator = None
        self.type = None

    def match(self, message: discord.message, user: discord.user = None) -> bool:
        if user is None:
            return message.id == self.message.id
        else:
            return message.id == self.message.id and user.id == self.creator.id

    def same_channel(self, message: discord.message):
        return message.channel.id == self.message.channel.id


class Jamble(Game):
    def __init__(self, message, answer, creator):
        super().__init__(message, answer, creator, "Jamble")


class AlbumGuess(Game):
    def __init__(self, message, answer, creator, images, final_image):
        super().__init__(message, answer, creator, "AlbumGuess")
        self.images = images
        self.final_image = final_image

    def reset(self):
        super().reset()
        self.images = None
