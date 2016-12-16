#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals

import json
from pymongo import MongoClient
from schema import Schema, Optional
from tools_lib.gtornado.escape import schema_unicode, schema_float, schema_objectid

PROD = '123.56.117.75'
DEV = '123.57.45.209'

# 存储 站点-时刻-配送员 的对应信息
# {time_table: { $elemMatch: { mans: {$elemMatch: {tel: { $regex: '91', $options: 'i' } } } }}}
mcn = MongoClient(host=DEV, port=27017)['aeolus']['node']


def models():
    node_schema = Schema({
        'name': schema_unicode,
        'loc': {
            'lat': schema_float,
            'lng': schema_float,
            'address': schema_unicode,
        },
        'point': {
            "type": "Point",
            "coordinates": [
                schema_float,  # lng
                schema_float,  # lat
            ]
        },
        'time_table': [
            {
                't': schema_unicode,
                'man': {
                    'id': schema_objectid,
                    'name': schema_unicode,
                    'tel': schema_unicode,
                    Optional('m_type', default='driver'): schema_unicode,
                    'client_id': schema_unicode
                }
            }
        ]
    })
    schedule_schema = Schema([
        {
            'man': {
                'id': schema_objectid,
                'name': schema_unicode,
                'tel': schema_unicode,
                Optional('m_type', default='driver'): schema_unicode,
                'client_id': schema_unicode
            },
            'run': [
                {
                    't': schema_unicode,
                    'name': schema_unicode,
                    'loc': {
                        'lat': schema_float,
                        'lng': schema_float,
                        'address': schema_unicode,
                    }
                }
            ]
        }
    ])


def add_geo(_mcn):
    print('\n给站点添加geo point:')
    cursor = _mcn.find({})
    for doc in cursor:
        point = {
            "type": "Point",
            "coordinates": [
                doc['loc']['lng'],  # lng
                doc['loc']['lat'],  # lat
            ]
        }
        result = _mcn.update_one({'_id': doc['_id']}, {'$set': {'point': point}, '$unset': {'geo': ''}})
        print('%s: %s' % (doc['name'], result.modified_count))


if __name__ == '__main__':
    add_geo(mcn)
