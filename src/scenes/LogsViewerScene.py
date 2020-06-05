from .BaseViewerScene import BaseViewerScene


class LogsViewerScene(BaseViewerScene):
    def __init__(self, session, redis):
        super().__init__()
        self.session = session
        self.redis = redis

    def fetch(self, start, end):
        return self.redis.lrange('logs', start, end)

    def items_count(self):
        return self.redis.llen('logs')
