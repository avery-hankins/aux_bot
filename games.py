import discord


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
