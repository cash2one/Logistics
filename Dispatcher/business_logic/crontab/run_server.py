# coding: utf-8
from __future__ import unicode_literals

import sys

import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

# 配置全局logging. => 配完PYTHON_PATH,在所有的import前做!!!
from tools_lib.common_util.log import init_log

init_log(os.path.dirname(os.path.abspath(__file__)))

import logging
import tornado.ioloop
from settings import MONGODB_NAME, config, run_at_day
from tools_lib.gmongoengine.connnection import connect
from task.utils import call_at_day


if __name__ == "__main__":
    connect(MONGODB_NAME, alias='aeolus_connection')

    io_loop = tornado.ioloop.IOLoop.current()
    # todo 从每隔N秒改成每隔N分钟运行 #
    for c in config:
        conf = list(c)
        logging.info("task [%s] periodic callback every [%s]sec", c[0].__name__, c[1])
        f = conf.pop(0)
        t = conf.pop(0) * 1000
        tornado.ioloop.PeriodicCallback(f, t).start()
        if conf.pop(0):
            f()

    # 每天N时刻运行 #
    for job in run_at_day:
        call_at_day(*job)

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
