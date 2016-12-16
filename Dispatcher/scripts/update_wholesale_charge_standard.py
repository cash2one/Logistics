#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals
from pymongo import MongoClient
from mysql.connector import connect


def ifnull(s, default=''):
    return default if s is None else s

if __name__ == '__main__':
    cnx = connect(host='182.92.158.10', port=3306, user='fengdevelop', password='dk@s3h%y7tr#c0z', charset='utf8')
    cursor = cnx.cursor(dictionary=True)

    shop_ids = [0, 13309, 12473, 12317, 12703, 13779, 12591, 13389, 13768, 13195, 13359, 13242, 12955, 12961, 13208,
                12907, 13816, 13820, 13818, 13829, 13847, 13822, 12757, 13486, 3831, 10971, 14778, 12823]
    sql = 'select s.*, o.tel ' \
          'from f_shop.shop s ' \
          'inner join f_shop.shop_owner o on s.shop_owner_id = o.id ' \
          'where s.id in (%s)' % ','.join(['%s'] * len(shop_ids))
    print sql
    cursor.execute(sql, shop_ids)

    # mc = MongoClient(host='123.57.45.209', port=27017)['wholesale']['charge_standard']
    mc = MongoClient(host='123.56.117.75', port=27017)['wholesale']['charge_standard']
    for record in cursor:
        print record['id'], record['shop_name']
        result = mc.update_one({'shop_id': record['id']}, {'$set': {'shop_name': record['shop_name']}})
        print result.modified_count
