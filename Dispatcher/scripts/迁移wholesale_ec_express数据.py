#!/usr/bin/env python
# coding:utf-8

from pymongo import MongoClient
import re
from tools_lib.transwarp.tz import utc_now
from multiprocessing.dummy import Pool

STATUS_CREATED_CREATED = 'CREATED.CREATED'
STATUS_CREATED_PAID = 'CREATED.PAID'
STATUS_SENDING_SENDING = 'SENDING.SENDING'
STATUS_SENDING_DELAY = 'SENDING.DELAY'
STATUS_FINISHED_FINISHED = 'FINISHED.FINISHED'
STATUS_FINISHED_NO_CASH = 'FINISHED.NO_CASH'
STATUS_FINISHED_CANCEL = 'FINISHED.CANCEL'
STATUS_FINISHED_REFUSE = 'FINISHED.REFUSE'
STATUS_FINISHED_TRASH = 'FINISHED.TRASH'

ss = {
    "NOCASH": dict(status="FINISHED", sub_status="NO_CASH"),
    "SORTED": dict(status="SENDING", sub_status="SENDING"),
    "SENDING": dict(status="SENDING", sub_status="SENDING"),
    "CLOSED": dict(status="FINISHED", sub_status="CANCEL"),
    "ADOPTED": dict(status="SENDING", sub_status="SENDING"),
    "WAREHOUSING": dict(status="SENDING", sub_status="DELAY"),
    "FINISHED": dict(status="FINISHED", sub_status="FINISHED"),
    "ERROR": dict(status="SENDING", sub_status="DELAY"),
    "CREATED": dict(status="CREATED", sub_status="CREATED")
}
regex = re.compile(".*测试.*")
start_num = '000000081007'
end_num = '000000087349'

DEV = '123.57.45.209'
PROD = '123.56.117.75'

mc_expr_old = MongoClient(host=PROD, port=27017)['wholesale_ec']['express']
mc_expr_new = MongoClient(host=PROD, port=27017)['aeolus']['express']

mc_trace_old = MongoClient(host=PROD, port=27017)['wholesale_ec']['expr_trace']
mc_trace_new = MongoClient(host=PROD, port=27017)['aeolus']['trace']


def move_express(expr_cursor):
    i = 0

    # ==> 迁移express
    for doc in expr_cursor:
        if mc_expr_new.find_one({'number': doc['expr_num']}):
            print(('运单[%s]已迁移.' % doc['expr_num']))
            continue
        i += 1
        print(('%s, %s, %s, %s' % (i, doc['expr_num'], doc['status'], doc['shop'].get('name'))))
        shop_id = doc['shop'].get('id')
        if shop_id == 15081 or (shop_id is None and doc['source'] == 'PHH'):
            shop_id = '56c2d708a785c90ab0014d06'
        expr_record = {
            "number": doc['expr_num'],
            "third_party": {
                "order_id": doc['source_order_id'],
                "name": doc['source']
            },
            "status": ss[doc['status']],
            "creator": {
                "tel": doc['shop'].get('tel', ''),
                "id": shop_id,
                "m_type": "",
                "name": doc['shop'].get('name', '')
            },
            "assignee": {
                "id": doc['courier'].get('id', ''),
                "name": doc['courier'].get('name', ''),
                "tel": doc['courier'].get('tel', ''),
                "m_type": "parttime"
            },
            "watchers": [
                {
                    "id": doc['courier'].get('id', ''),
                    "name": doc['courier'].get('name', ''),
                    "tel": doc['courier'].get('tel', ''),
                    "m_type": "parttime"
                },
                {
                    "id": doc['urban_driver'].get('id', ''),
                    "name": doc['urban_driver'].get('name', ''),
                    "tel": doc['urban_driver'].get('tel', ''),
                    "m_type": "area_manager"
                }
            ],
            "node": {
                "node_n": {
                    "real_tel": doc['receiver'].get('real_tel', ''),
                    "name": doc['receiver'].get('name', ''),
                    "tel": doc['receiver'].get('tel', ''),
                    "addr": doc['receiver'].get('address', ''),
                    "lat": doc['receiver'].get('lat', 0.0),
                    "lng": doc['receiver'].get('lng', 0.0),
                    "fence": {
                        "id": doc['node']['id'],
                        "name": doc['node']['name']
                    },
                    # "msg": doc['receiver'].get('msg', '')
                },
                "node_0": {
                    "name": "",
                    "tel": "",
                    "addr": "",
                    "lat": 0.0,
                    "lng": 0.0
                }
            },
            "fee": {
                "fh": doc['fee']['cost'],
                "ps": doc['fee']['order']
            },
            "times": {

            },
            "create_time": doc['create_time'],
            "update_time": doc.get('update_time', utc_now()),
            "remark": ""
        }
        mc_expr_new.insert(expr_record)
        # break


def move_trace(trace_cursor):
    # ==> 迁移expr_trace
    i = 0

    for doc in trace_cursor:
        # expr_num = doc['_id']
        # 处理trace重复迁移
        if mc_trace_new.find_one({'number': doc['expr_num']}):
            print(('运单[%s]trace已迁移.' % doc['expr_num']))
            continue
        i += 1
        print(('%s, %s' % (i, doc['expr_num'])))
        cursor = mc_trace_old.find({'expr_num': doc['expr_num']})
        traces = [{
                      "number": t['expr_num'],
                      "from_status": "",
                      "to_status": t['status'] if t['status'] in ('CREATED', 'FINISHED') else 'SENDING',
                      "event": "",
                      "event_source": "",
                      "operator": t.get('operator', {}),
                      "msg": t.get('msg', ''),
                      "create_time": t['actual_time']
                  } for t in cursor]
        mc_trace_new.insert_many(traces)


if __name__ == '__main__':
    pool = Pool(4)
    # ==> 迁移express
    e_cursor = mc_expr_old.find(
        {'expr_num': {'$gte': start_num, '$lt': end_num}, "shop.name": {'$not': regex}, 'source': {'$ne': 'lazycat'}})
    pool.map(move_express, [e_cursor])

    # ==> 迁移expr_trace
    pipe = [
        {
            "$match": {
                "expr_num": {"$gte": start_num, '$lt': end_num}
            }
        },
        {
            "$group": {
                '_id': '$expr_num',
                "expr_num": {'$first': '$expr_num'}
            }
        }
    ]
    t_cursor = mc_trace_old.aggregate(pipeline=pipe)
    pool.map(move_trace, [t_cursor])
