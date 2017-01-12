#! /usr/bin/env python
# -*- coding: utf-8 -*-


import sys
from multiprocessing.dummy import Pool

import os
import imp

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)))

from tools_lib.common_util.archived.gtz import TimeZone
from settings import *
from mongoengine import *
from pymongo import MongoClient
from handlers.models import *
from tools_lib.common_util.sstring import safe_join

imp.reload(sys)
sys.setdefaultencoding("utf-8")
PROD_MONGODB_OUTER_IP = '123.56.117.75'
MONGODB_CONFIG = {
    # 'host': DEV_OUTER_IP,
    'host': PROD_MONGODB_OUTER_IP,
    'port': 27017,
}


def pprint(*arg):
    print((safe_join(arg)))


def sign_in():
    sign_in = client['profile']['sign_in']
    start, end = TimeZone.day_range(value=TimeZone.local_now())
    pprint("姓名", "电话", "时间", "地址", "POI", "经度", "维度", )
    for doc in sign_in.find({"create_time": {"$gte": start, "$lte": end}}):
        pprint(doc['name'], doc['tel'], TimeZone.utc_to_local(doc['create_time']), doc['loc']['addr'],
               doc['loc']['name'], doc['loc']['lng'], doc['loc']['lat'])


if __name__ == '__main__':
    print((MONGODB_NAME, MONGODB_CONFIG))
    from functools import partial

    pool = Pool(8)
    client = MongoClient(**MONGODB_CONFIG)
    conn = client['wholesale_ec']['expr_trace']
    expr_conn = client['wholesale_ec']['express']
    connect(MONGODB_NAME, alias="aeolus_connection", **MONGODB_CONFIG)

    sign_in()
    # d = []
    # with open("./data") as f:
    #     for line in f:
    #         line = line.strip().split('\t')
    #         d.append(line)
    #
    #
    # def handle(i):
    #     expr = Express.objects(number="0000000"+i[0]).first()
    #     if not expr:
    #         return
    #
    #     return expr.number, i[1], expr.fee['fh']
    #
    # ret = pool.map(handle, d)
    # for _ in ret:
    #     print safe_join("\t", _)
