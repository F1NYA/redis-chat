from src.definitions import Set

from .BaseViewerScene import BaseViewerScene


class DeliveredMessagesViewerScene(BaseViewerScene):
    def __init__(self, session, redis):
        super().__init__()
        self.session = session
        self.redis = redis
        self.queue_name = "%s:%s" % (Set.DELIVERED_MESSAGES, self.session["me"].login)

    def fetch(self, start, end):
        return self.redis.zrange(self.queue_name, start, end)

    def items_count(self):
        return self.redis.zcard(self.queue_name)
