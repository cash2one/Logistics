#! /usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

import sys

import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
from tools_lib.common_util.log import init_log

# 配置全局logging. => 配完PYTHON_PATH,在所有的import前做!!!
init_log(os.path.dirname(os.path.abspath(__file__)))

import logging
import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.options import define, options
from urls import urls
from settings import settings, MONGODB_NAME
from tools_lib.gmongoengine.connnection import connect

define("port", default=5004, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        connect(MONGODB_NAME, alias='coolie_connection')
        tornado.web.Application.__init__(self, urls, **settings)

    def log_request(self, handler):
        """Writes a completed HTTP request to the logs.

        By default writes to the python root logger.  To change
        this behavior either subclass Application and override this method,
        or pass a function in the application settings dictionary as
        ``log_function``.
        """
        if "log_function" in self.settings:
            self.settings["log_function"](handler)
            return
        if handler.get_status() < 400:
            log_method = logging.info
        elif handler.get_status() < 500:
            log_method = logging.warning
        else:
            log_method = logging.error
        request_time = 1000.0 * handler.request.request_time()
        log_method("[timeit] [%s] [%s][%s][%s bytes] [%s]: [%d msecs]" %
                   (handler.request.remote_ip, handler.request.method, handler.request.uri,
                    handler._headers._dict.get('Content-Length', 0), handler.get_status(), request_time))


if __name__ == "__main__":
    options.parse_command_line()
    application = Application()

    server = tornado.httpserver.HTTPServer(application, xheaders=True)
    server.listen(options.port)
    logging.info("I am working at port %s" % options.port)

    io_loop_ = tornado.ioloop.IOLoop.current()
    try:
        io_loop_.start()
    except KeyboardInterrupt:
        io_loop_.stop()
