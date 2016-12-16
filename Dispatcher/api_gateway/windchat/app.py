#!/usr/bin/env python
#coding=utf-8
__author__ = 'kk'

import os
import sys
from logging import info
from leancloud import init

# 下面这句话一定要放在tools_lib之前
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import tornado.web
import tornado.ioloop
import tornado.httpclient
import tornado.httpserver
import tornado.escape
import tornado.options
from tornado.options import define, options
from tools_lib.leancloud.credentials import credentials

define("port", default=5556, help="run on the given port", type=int)
# initiate LeanCloud SDK
init(**credentials)


class Application(tornado.web.Application):

    def __init__(self):
        from urls import urls
        from settings import settings
        tornado.web.Application.__init__(self, urls, **settings)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    application = Application()

    server = tornado.httpserver.HTTPServer(application)
    server.listen(options.port)
    info("WindChat API Gateway")
    info("Listening to port %s..." % (options.port))

    io_loop_ = tornado.ioloop.IOLoop.current()
    io_loop_.start()
