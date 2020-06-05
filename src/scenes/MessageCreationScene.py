from src.definitions import Storage
from src import Message

from .BaseScene import BaseScene


class MessageCreationScene(BaseScene):
    def __init__(self, session, redis):
        super(MessageCreationScene, self).__init__(
            [
                {
                    "type": "list",
                    "name": "receiver",
                    "message": "Who do you want to send a letter to?",
                    "choices": self.load_users,
                },
                {
                    "type": "input",
                    "name": "body",
                    "message": "Enter message text?",
                    "default": lambda answers: "Hi, %s" % answers["receiver"],
                },
                {"type": "confirm", "name": "confirm", "message": "Confirm?"},
            ]
        )
        self.session = session
        self.redis = redis

    def load_users(self, *args):
        user_keys = self.redis.keys("%s:*" % Storage.USERS)
        return list(map(lambda v: "".join(v.split(":")[1:]), user_keys))

    def enter(self):
        answers = self.ask()
        if not answers["confirm"]:
            return

        self.session["chat"].publish_message(
            Message(
                author=self.session["me"].login,
                receiver=answers["receiver"],
                body=answers["body"],
            )
        )
