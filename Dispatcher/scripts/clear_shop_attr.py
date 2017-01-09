#!/usr/bin/env python
# coding:utf-8

from pymongo import MongoClient

if __name__ == "__main__":
    # mc = MongoClient(host='123.57.45.209', port=27017)['profile']['shop']
    mc = MongoClient(host='123.56.117.75', port=27017)['profile']['shop']

    # for doc in mc.find({}):
    #     print(doc)
    #     shop_id = doc['_id']
    #     result = mc.update_many({'_id': shop_id}, {'$unset': {'accounts': 1}})
    #     print result.modified_count
    result = mc.update_many({}, {'$unset': {'biz_type': 1, 'deprecated': ''}})
    print((result.modified_count))
