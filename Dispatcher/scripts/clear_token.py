#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals
# from tools_lib.gedis.gedis import Redis
import redis

redis_client = redis.StrictRedis(host='10.173.14.210', port=6379, db=0, password='tT6WyYJ5BjkHgNrDblILf18UuieSnsap')
keys = redis_client.keys("man:token:*")
for k in keys:
    if redis_client.get(k) in (
            "56c66f1c7f452563e439bca4", "56e17b28eed093310861162b", "56f4e40ceed0932e4a19c027",
            "56c811a27f452563e439bcb6",
            "56fb30b5eed093338d22a919", "56c7c2527f452563e439bcb3", "5705d790eed093542eb1ea11",
            "56fb5435eed0931146f39762"):
        print(k, redis_client.delete(k))
