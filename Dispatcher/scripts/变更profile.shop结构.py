#!/usr/bin/env python
# coding:utf-8
from multiprocessing.dummy import Pool
from pymongo import MongoClient
from bson import ObjectId

PROD = '123.56.117.75'
DEV = '123.57.45.209'

mc_from = MongoClient(host=PROD, port=27017)['profile']['shop']
mc_to = MongoClient(host=PROD, port=27017)['profile']['shop']


def move_fields(charge_cursor):
    i = 0
    for c in charge_cursor:
        c_shop_id = c['_id']
        c_shop_name = c.get('name', '')
        loc = c['loc']
        lat = float(loc.get('latitude', 0.0))
        lng = float(loc.get('longitude', 0.0))

        # if mc_to.find_one({'fee.fh_base': {'$exists': True}}):
        #     print(u'[%s]已迁移.' % c_shop_name)
        #     continue

        i += 1
        result = mc_to.update_one({'_id': c_shop_id},
                                  {'$set': {
                                      'loc': {'latitude': lat, 'longitude': lng, 'address': loc.get('address', '')}
                                  }}
                                  )
        print(('%s, %s, %s, lat:%s, lng:%s, %s, %s' % (
            i, c_shop_id, c_shop_name, lat, lng, result.matched_count, result.modified_count)))


if __name__ == '__main__':
    pool = Pool(4)
    # ==> 迁移商户业务需求到shop的document内部
    e_cursor = mc_from.find({'loc.latitude': {'$type': 2}})
    pool.map(move_fields, [e_cursor])
