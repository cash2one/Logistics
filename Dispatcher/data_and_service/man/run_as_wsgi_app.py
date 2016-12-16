#!/usr/bin/env python
# coding:utf-8

"""
A WSGI application entry.
"""
import logging
import sys

import os

# === 模块自己的PYTHON_PATH, 让代码找到正确的tools_lib. ==>要在所有import前做!!!
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from tools_lib.common_util.log import init_log
# === 配置全局logging. ==> 配完PYTHON_PATH,在所有的import前做!!!
init_log(os.path.dirname(os.path.abspath(__file__)))

from tools_lib.transwarp import db
from tools_lib.transwarp.web import WSGIApplication
from mongoengine import connect
from model_logics.config import CONFIGS
import rest_api


# init mysql:
db.create_engine(**CONFIGS.mysql)
# init mongodb: https://jira.mongodb.org/browse/PYTHON-986
connect(host=CONFIGS.mongodb, alias='profile_connection', connect=False)
logging.info("Init mongodb with %s", CONFIGS.mongodb)

# init wsgi app:
wsgi_app = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))

wsgi_app.add_module(rest_api)


if __name__ == '__main__':
    wsgi_app.run(6002, host='0.0.0.0')
else:
    # init log does not work here.
    print "\n@@@ uWSGI @@@\n"
    application = wsgi_app.get_wsgi_application()
