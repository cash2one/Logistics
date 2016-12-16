#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals
from pymongo import MongoClient
from step_1_csv_to_schedule import dump_to_schedule
from step_2_synchronization_check import schedule_to_node, node_to_schedule
from step_3_add_point_to_node import add_geo

# PROD = '123.56.117.75'
DEV = '123.57.45.209'

if __name__ == '__main__':
    host = DEV
    mcs = MongoClient(host=host, port=27017)['aeolus']['schedule']
    mcn = MongoClient(host=host, port=27017)['aeolus']['node']

    # 清理数据库
    mcs.remove({})
    mcn.remove({})

    # 导数据
    dump_to_schedule('csv_to_schedule-dev.csv', mcs)
    schedule_to_node(mcs, mcn, is_check=False)
    add_geo(mcn)
    # 导完, 做一遍校验
    schedule_to_node(mcs, mcn, is_check=True)
    node_to_schedule(mcn, mcs)
