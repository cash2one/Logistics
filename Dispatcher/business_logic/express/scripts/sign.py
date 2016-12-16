#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys

import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)))
import logging
from settings import *
from pymongo import MongoClient
from handlers.models import *
from tools_lib.common_util.sstring import safe_join

reload(sys)
sys.setdefaultencoding("utf8")

PROD_MONGODB_OUTER_IP = '123.56.117.75'
MONGODB_CONFIG = {
    # 'host': DEV_OUTER_IP,
    'host': PROD_MONGODB_OUTER_IP,
    'port': 27017,
}

logging.root.level = logging.NOTSET

# 初始化链接
client = MongoClient(**MONGODB_CONFIG)
crontab_conn = client['aeolus']['crontab']

if __name__ == '__main__':
    print MONGODB_NAME, MONGODB_CONFIG
    shop_conn = client['profile']['shop']
    for doc in shop_conn.find():
        print safe_join([doc.get('name', "空"), doc['tel'], doc.get("fee", {}).get("fh_base", 15)])
