# -*- coding:utf-8 -*-
import os
from celery import Celery, platforms
import sys

# === 模块自己的PYTHON_PATH, 让代码找到正确的tools_lib. ==>要在所有import前做!!!
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from tools_lib.host_info import *

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '../..')

# 是否是DEBUG模式
DEBUG = platform.node() not in (PROD_API_NODE,)

app = Celery('mq')
app.config_from_object('config')
# 解决celery在supervisor下不能用root用户启动的限制，虽然用root启动不是最佳实践
platforms.C_FORCE_ROOT = True

if __name__ == '__main__':
    app.start()
