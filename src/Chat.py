from src.definitions import Set, Storage, MessageStatus, MessageEvent
from src import Message
from time import time


def now():
    return round(time() * 1000)


class Chat:
    def __init__(self, redis):
        self.redis = redis

    def publish_message(self, message):
        pipe = self.redis.pipeline()
        message.save(pipe)

        author = message.author
        id = message.id

        pipe.publish('%s:%s' % (MessageEvent.CREATED, author), id)
        pipe.sadd(Set.UNPROCESSED_MESSAGES, id)
        pipe.zadd('%s:%s' % (Set.SENT_MESSAGES, author), {id: now()})
        pipe.zadd(
            '%s:%s' % (Set.WAIT_MODERATING_MESSAGES, author),
            {id: now()},
        )
        pipe.lpush(
            'logs', 'user "%s" publish message "%s"' % (author, id),
        )

        pipe.execute()

    def listen_events(self, events_handlers):
        pipe = self.redis.pubsub()
        pipe.psubscribe(**events_handlers)
        thread = pipe.run_in_thread(sleep_time=0.001)

        return thread

    def get_next_unprocessed_message(self, admin_login):
        mid = self.redis.srandmember(Set.UNPROCESSED_MESSAGES, 1)
        if not mid or not mid[0]:
            return

        mid = mid[0]

        message = Message.load(mid, self.redis)

        message_key = '%s:%s' % (Storage.MESSAGES, mid)
        author = self.redis.hget(message_key, 'author')

        pipe = self.redis.pipeline()
        pipe.srem(Set.UNPROCESSED_MESSAGES, mid)
        pipe.zrem('%s:%s' % (Set.WAIT_MODERATING_MESSAGES, author), mid)

        message.status = MessageStatus.MODERATING
        message.save(pipe)

        pipe.zadd('%s:%s' % (Set.MODERATING_MESSAGES, author), {mid: now()})
        pipe.lpush(
            'logs', '"%s" took message "%s" on moderation' % (admin_login, mid),
        )

        pipe.execute()

        return message

    def confirm_message(self, admin_login, message):
        pipe = self.redis.pipeline()

        message.status = MessageStatus.CONFIRMED
        message.save(pipe)

        created_at = message.created_at
        receiver = message.receiver
        author = message.author
        id = message.id

        pipe.srem(Set.UNPROCESSED_MESSAGES, id)
        pipe.lpush(
            'logs', 'admin "%s" approve message "%s"' % (admin_login, id),
        )
        pipe.zrem('%s:%s' % (Set.MODERATING_MESSAGES, author), id)
        pipe.zadd(
            '%s:%s' % (Set.CONFIRMED_MESSAGES, author), {id: now()},
        )
        pipe.zincrby(Set.ACTIVE_SENDERS, 1, author)
        pipe.zadd(
            '%s:%s' % (Set.PENDING_MESSAGES, receiver), {id: created_at},
        )
        pipe.publish('%s:%s' % (MessageEvent.CONFIRMED, author), id)
        pipe.publish('%s:%s' % (MessageEvent.PENDING, receiver), id)

        pipe.execute()

    def ban_message(self, admin_login, message):
        pipe = self.redis.pipeline()

        message.status = MessageStatus.BANNED
        message.save(pipe)

        author = message.author
        id = message.id

        pipe.srem(Set.UNPROCESSED_MESSAGES, id)
        pipe.zrem('%s:%s' % (Set.MODERATING_MESSAGES, author), id)
        pipe.zadd('%s:%s' % (Set.BANNED_MESSAGES, author), {id: now()})
        pipe.zincrby(Set.BANNED_USERS, 1, author)
        pipe.publish('%s:%s' % (MessageEvent.BANNED, author), id)
        pipe.lpush('logs', 'admin "%s" block message "%s"' % (admin_login, id))

        pipe.execute()

    def read_message(self, message):
        if not message:
            return

        pipe = self.redis.pipeline()

        message.status = MessageStatus.READ
        message.save(pipe)

        receiver = message.receiver
        author = message.author
        id = message.id

        pipe.zrem('%s:%s' % (Set.CONFIRMED_MESSAGES, author), id)
        pipe.sadd('%s:%s' % (Set.READ_MESSAGES, receiver), id)
        pipe.zadd('%s:%s' % (Set.DELIVERED_MESSAGES, author), {id: now()})
        pipe.lpush('logs', 'user "%s" read message "%s"' % (receiver, id))
        pipe.publish('%s:%s' % (MessageEvent.DELIVERED, author), id)

        pipe.execute()
