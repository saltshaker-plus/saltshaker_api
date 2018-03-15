import redis
import configparser
import os

config = configparser.ConfigParser()
conf_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
config.read(conf_path + "/saltshaker.conf")
redis_host = config.get("Redis", "REDIS_HOST")
redis_port = config.get("Redis", "REDIS_PORT")
redis_db = config.get("Redis", "REDIS_DB")
redis_pwd = config.get("Redis", "REDIS_PASSWORD")

redisConnect = redis.StrictRedis(redis_host, redis_port, redis_db, redis_pwd)


class RedisTool:
    @staticmethod
    def hexists(name, key):
        return redisConnect.hexists(name, key)

    @staticmethod
    def hget(name, key):
        return redisConnect.hget(name, key)

    @staticmethod
    def getset(name, value):
        return redisConnect.getset(name, value)

    @staticmethod
    def hdel(name, *keys):
        return redisConnect.hdel(name, *keys)

    @staticmethod
    def hgetall(name):
        return redisConnect.hgetall(name)

    @staticmethod
    def hkeys(name):
        return redisConnect.hkeys(name)

    @staticmethod
    def hlen(name):
        return redisConnect.hlen(name)

    @staticmethod
    def hset(name, key, value):
        return redisConnect.hset(name, key, value)

    @staticmethod
    def setex(name, time, value):
        return redisConnect.setex(name, time, value)

    @staticmethod
    def get(name):
        return redisConnect.get(name)

    @staticmethod
    def exists(name):
        return redisConnect.exists(name)

    @staticmethod
    def set(name, value):
        return redisConnect.set(name, value)

    @staticmethod
    def expire(name, time):
        return redisConnect.expire(name, time)
