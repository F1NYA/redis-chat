from src.definitions import Set

from .BaseViewerScene import BaseViewerScene


class SendersViewerScene(BaseViewerScene):
    def __init__(self, session, redis):
        super().__init__()
        self.session = session
        self.redis = redis

    def fetch(self, start, end):
        senders = self.redis.zrange(Set.ACTIVE_SENDERS, start, end, withscores=True)
        return list(map(lambda t: '"%s" with %i messages' % (t[0], t[1]), senders))

    def items_count(self):
        return self.redis.zcard(Set.ACTIVE_SENDERS)
