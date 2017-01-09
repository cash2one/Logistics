#!/usr/bin/env python
# coding:utf-8


from multiprocessing.dummy import Pool

from pymongo import MongoClient
from tools_lib.common_util.archived.gtz import TimeZone

DEV = '123.57.45.209'
PROD = '123.56.117.75'

mc = MongoClient(host=PROD, port=27017)['aeolus']['express']


def modify_sj_time(expr_cursor):
    i = 0
    for doc in expr_cursor:
        i += 1
        times = []
        _times = []
        for k, t in list(doc['times'].items()):
            if k != 'sj_time':
                times.append(t)

        times = sorted(times)
        for t in times:
            _times.append(TimeZone.datetime_to_str(t, pattern='%H:%M'))

        sj_time = min(times)
        result = mc.update_one({'_id': doc['_id']}, {'$set': {'times.sj_time': sj_time}})
        print(('%s, %s, min%s => [%s], %s, %s'
              % (i, doc['number'], _times, TimeZone.datetime_to_str(sj_time, pattern='%H:%M'),
                 result.matched_count, result.modified_count)))


if __name__ == '__main__':
    pool = Pool(4)
    cursor = mc.find({'times.sj_time': {'$exists': True},
                      'create_time': {'$gte': TimeZone.str_to_datetime("2016-05-01T00:00:00.000+0800")}})
    modify_sj_time(expr_cursor=cursor)
    # pool.map(modify_sj_time, [cursor])
