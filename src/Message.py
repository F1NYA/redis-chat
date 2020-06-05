from src.definitions import Storage, MessageStatus as MessageStatus
from time import time


class Message:
    def __init__(
        self,
        author,
        receiver,
        body,
        id=None,
        status=MessageStatus.CREATED,
        created_at=round(time() * 1000),
    ):
        self.author = author
        self.receiver = receiver
        self.body = body
        self.status = status
        self.created_at = created_at
        self.id = id or self.get_id()

    @staticmethod
    def load(mid, redis):
        serialized_message = redis.hgetall("%s:%s" % (Storage.MESSAGES, mid))
        if not serialized_message:
            return None
        print(serialized_message)
        return Message(**serialized_message)

    def get_id(self):
        return "%s:%s:%i" % (self.author, self.receiver, self.created_at)

    def to_dict(self):
        return {
            "id": self.id,
            "body": self.body,
            "status": self.status,
            "author": self.author,
            "receiver": self.receiver,
            "created_at": self.created_at,
        }

    def save(self, redis):
        redis.hmset("%s:%s" % (Storage.MESSAGES, self.id), self.to_dict())
