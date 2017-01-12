#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-09-07 15:49:13
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo

import os
import sys
import logging

# 下面这句话一定要放在tools_lib之前
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

# from tools_lib.log import init_log
#
# init_log(os.path.dirname(os.path.abspath(__file__)))

import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
from tornado.options import define, options
# from raven.contrib.tornado import AsyncSentryClient

define("port", default=5555, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        from .urls import urls
        from .settings import MONGODB_NAME, settings
        from tools_lib.gmongoengine.connnection import connect
        connect(MONGODB_NAME)
        tornado.web.Application.__init__(self, urls, **settings)

        # self.sentry_client = AsyncSentryClient(RAVEN_DSN)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    application = Application()

    server = tornado.httpserver.HTTPServer(application)
    server.listen(options.port)
    logging.info("I am working at port %s" % (options.port))

    io_loop_ = tornado.ioloop.IOLoop.current()
    io_loop_.start()
