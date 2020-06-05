from src.definitions import Set

from .BaseViewerScene import BaseViewerScene


class SpammersViewerScene(BaseViewerScene):
    def __init__(self, session, redis):
        super().__init__()
        self.session = session
        self.redis = redis

    def fetch(self, start, end):
        users = self.redis.zrange(Set.BANNED_USERS, start, end, withscores=True)
        return list(map(lambda t: '"%s" with %i spams' % (t[0], t[1]), users))

    def items_count(self):
        return self.redis.zcard(Set.BANNED_USERS)
