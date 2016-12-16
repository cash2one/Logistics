#!/usr/bin/env python
#coding=utf-8
__author__ = 'kk'

import os
import sys
from logging import info, debug, warn, error

# 下面这句话一定要放在tools_lib之前
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import tornado.web
import tornado.ioloop
import tornado.httpclient
import tornado.httpserver
import tornado.escape
from tornado.options import define, options, parse_command_line
from leancloud.client import init
from tools_lib.leancloud.credentials import credentials

# initiate LeanCloud SDK
init(**credentials)
define("port", default=5555, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        from urls import urls
        from settings import MONGODB_NAME, MONGODB_CONFIG, settings
        from mongoengine import connect
        connect(MONGODB_NAME, **MONGODB_CONFIG)
        tornado.web.Application.__init__(self, urls, **settings)

if __name__ == "__main__":
    parse_command_line()
    application = Application()

    server = tornado.httpserver.HTTPServer(application)
    server.listen(options.port)
    info("WindChat Core")
    info("Listening to port %s..." % options.port)
    io_loop_ = tornado.ioloop.IOLoop.current()
    io_loop_.start()
