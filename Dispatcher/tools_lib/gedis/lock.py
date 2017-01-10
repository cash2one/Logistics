# -*- coding:utf-8 -*-
import time
import uuid
from .gedis import Redis


class LockTimeout(Exception): pass


class Lock(object):
    def __init__(self, key="", ttl=40, timeout=10, interval=0.03):
        """
        :param key:
        :param ttl: expire time(锁最大过期时间) / s
        :param timeout: timeout(阻塞最大时间) / s
        :param interval: sleep interval(睡眠间隔) / s
        :return:
        Usage::

            with Lock('my_lock'):
                print "Critical section"
        """
        self.redis_client = Redis()
        self.key = "redis:lock:" + key
        self.ttl = ttl
        self.timeout = timeout
        self.interval = interval
        # generate a unique UUID
        self.value = uuid.uuid1().get_hex()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def acquire(self):
        timeout = self.timeout
        if timeout == 0:
            while True:
                if self.redis_client.set(self.key, self.value, ex=self.ttl, nx=True):
                    return True
                time.sleep(self.interval)
        else:
            while timeout >= 0:
                if self.redis_client.set(self.key, self.value, ex=self.ttl, nx=True):
                    return True
                timeout -= self.interval
                time.sleep(self.interval)
            raise LockTimeout("Timeout whilst waiting for lock")

    def release(self):
        if self.redis_client.get(self.key) == self.value:
            # only unlock myself lock
            return self.redis_client.delete(self.key)
        return 0

