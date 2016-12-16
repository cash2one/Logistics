# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import sys

import os

# === 模块自己的PYTHON_PATH, 让代码找到正确的tools_lib. ==>要在所有import前做!!!
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)))

from tools_lib.common_util.rabbitmq_client import EXCHANGE_SEND_SMS, RabbitMqCtl
try:
    import cPickle as pickle
except:
    import pickle

if __name__ == '__main__':
    message = ' '.join(sys.argv[1:]) or pickle.dumps({'tel': '15067125727', 'msg': 'hello,world你好'})
    RabbitMqCtl.basic_publish(exchange=EXCHANGE_SEND_SMS, body=message)
