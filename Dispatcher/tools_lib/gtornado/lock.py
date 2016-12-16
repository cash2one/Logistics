#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-11-12 15:08:43
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo

from tornado import gen
import uuid
from tools_lib.gedis.gedis import Redis
from tornado.concurrent import Future
from tornado import ioloop
from tornado import locks


class DDosError(Exception): pass


class AsyncAntiDDosLock(object):
    def __init__(self, key="", ttl=30):
        """
        :param key:
        :param ttl: redis key expire time(锁最大过期时间) / s
        :return:
        Usage::

            with (yield AsyncAntiDDosLock('my_lock').acquire()):
                print "Critical section"
        """
        self.redis_client = Redis()
        self.key = "redis:lock:anti-DDos:" + str(key)
        self.ttl = ttl
        # generate a unique UUID
        self.value = uuid.uuid1().get_hex()

    def acquire(self):
        """Decrement the counter. Returns a Future.

        Block if the counter is zero and wait for a `.release`. The Future
        raises `.TimeoutError` after the deadline.
        """
        waiter = Future()
        if self.redis_client.set(self.key, self.value, ex=self.ttl, nx=True):
            waiter.set_result(locks._ReleasingContextManager(self))
        else:
            waiter.set_exception(DDosError("被暴击了"))
        # def on_timeout():
        #     waiter.set_exception(gen.TimeoutError())
        # io_loop = ioloop.IOLoop.current()
        # timeout_handle = io_loop.add_timeout(timeout, on_timeout)
        # waiter.add_done_callback(
        #     lambda _: io_loop.remove_timeout(timeout_handle))
        return waiter

    def release(self):
        if self.redis_client.get(self.key) == self.value:
            self.redis_client.delete(self.key)

    def __enter__(self):
        raise RuntimeError(
            "Use AsyncLock like 'with (yield AsyncLock().acquire())', not like"
            " 'with AsyncLock()'")

    __exit__ = __enter__
