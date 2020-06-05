from src.definitions import Storage, Set


class User:
    def __init__(self, login, role, redis):
        self.login = login
        self.role = role
        self.redis = redis

        pipe = self.redis.pipeline()
        pipe.lpush('logs', 'user "%s" login' % self.login)
        pipe.zincrby(Set.ONLINE_USERS, 1, self.login)
        pipe.execute()

    @staticmethod
    def load(redis, login):
        user = redis.hgetall("%s:%s" % (Storage.USERS, login))
        if not user:
            return None

        return User(user["login"], user["role"], redis)

    def save(self):
        pipe = self.redis.pipeline()
        pipe.hmset(
            "%s:%s" % (Storage.USERS, self.login),
            {"login": self.login, "role": self.role},
        )
        pipe.execute()

    def __del__(self):
        results = (
            self.redis.pipeline()
            .lpush('logs', 'user "%s" logout' % self.login)
            .zincrby(Set.ONLINE_USERS, -1, self.login)
            .execute()
        )
        if not results[1]:
            self.redis.zrem(Set.ONLINE_USERS, self.login)
