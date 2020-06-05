from src.definitions import Storage, Set, MessageStatus

from .BaseViewerScene import BaseViewerScene


class SentMessagesViewerScene(BaseViewerScene):
    def __init__(self, session, redis):
        super().__init__()
        self.session = session
        self.redis = redis
        self.queue_name = '%s:%s' % (Set.SENT_MESSAGES, self.session['me'].login)

    def fetch(self, start, end):
        messages = self.redis.zrange(self.queue_name, start, end)
        return list(map(self.map_messages_statuses, messages))

    def items_count(self):
        return self.redis.zcard(self.queue_name)

    def map_messages_statuses(self, mid):
        status = self.redis.hget('%s:%s' % (Storage.MESSAGES, mid), 'status')
        status_str = '"%s" %s' % (mid, status)

        if status == MessageStatus.BANNED:
            status_str = '❗️ ' + status_str
        elif status == MessageStatus.CONFIRMED:
            status_str = '✅ ' + status_str
        else:
            status_str = '📪 ' + status_str

        return status_str
