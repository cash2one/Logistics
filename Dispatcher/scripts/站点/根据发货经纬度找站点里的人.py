#!/usr/bin/env python
# coding:utf-8


import json

from pymongo import MongoClient

PROD = '123.56.117.75'
DEV = '123.57.45.209'

# 存储 站点-时刻-配送员 的对应信息
mc = MongoClient(host=PROD, port=27017)['aeolus']['node']

if __name__ == '__main__':
    cursor = mc.find({
        'point': {
            '$near': {
                '$geometry': {
                    'type': "Point",
                    'coordinates': [120.1949550000, 30.1830070000]
                },
                '$maxDistance': 1000,
            }}})
    for doc in cursor:
        doc.pop('_id')
        mans = {(t['man']['client_id'], t['man']['name']) for t in doc['time_table'] if t['man']['m_type'] == 'man'}
        print((json.dumps(list(mans), ensure_ascii=False, indent=2)))
