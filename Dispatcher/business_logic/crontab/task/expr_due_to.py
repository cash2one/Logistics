# coding:utf-8


import json
import arrow
import logging
from bson import ObjectId

from tools_lib import java_windlog
from .utils import cron_conn, expr_conn, call_conn
from tools_lib.bl_expr import ExprState


def expr_due_to():
    time_now = arrow.now()

    if time_now.hour < 8 and time_now.minute < 30:
        pass

    # express
    exprs_processed = [ObjectId(i["ref_id"]) for i in cron_conn.find({"name": "express"}, {'ref_id': 1})]
    exprs = expr_conn.find({
        "_id": {"$nin": exprs_processed},
        "times.due_time": {"$lte": time_now.shift(minutes=+120).datetime, "$gt": time_now.shift(minutes=-1).datetime},
    })
    for expr in exprs:
        cases = []
        creator = expr['creator']
        sender = expr['node']['node_0']
        receiver = expr['node']['node_n']
        due_time = expr.get("times", {}).get("due_time", None)
        create_time = expr['create_time']
        msg = ''
        # 如果是立即下单(非预约单), 不去写日志
        if due_time == create_time:
            msg = 'Got express[%s], not an appointment one, skipped' % expr['number']
            logging.info(msg)
        # 如果是预约单, 去写日志
        else:
            case = {
                "shopId": creator['id'],
                "shopName": creator.get('name', ''),
                "shopTel": creator.get('tel', ''),
                "sender": {
                    "id": sender['id'],
                },
                "receiver": {
                    "id": receiver['id'],
                },
                "orderId": expr['number'],
                "orderUserType": expr['mode'],
                "dueTime": arrow.get(due_time).to('local').replace(microsecond=0).isoformat() if due_time else None
            }
            cases.append(case)
            java_windlog.log_create(
                type='21010',
                shopId=sender["id"],
                caseDetail=json.dumps(cases, ensure_ascii=False),
                createTime=arrow.get(create_time).to('local').replace(microsecond=0).isoformat(),
            )
            msg = 'Got express[%s], 21010 log sent' % expr['number']
            logging.info(msg)

        # 即使是跳过的也是处理过了.
        cron_conn.insert({
            "create_time": time_now.datetime,
            "name": "express",
            "ref_id": str(expr['_id']),
            'msg': msg
        })

    # call
    calls_processed = [ObjectId(i["ref_id"]) for i in cron_conn.find({"name": "call"}, {'ref_id': 1})]
    calls = call_conn.find({
        "due_time": {"$lte": time_now.shift(minutes=+120).datetime, "$gt": time_now.shift(minutes=-1).datetime},
        "_id": {"$nin": calls_processed}
    })
    for call in calls:
        sender = call['sender']
        due_time = call["due_time"]
        create_time = call['create_time']
        java_windlog.log_create(
            type='21001',
            shopId=call["shop_id"],
            amount=call["count"],
            creatorId=sender["id"],
            orderUserType=ExprState.MODE_SHORT,
            caseDetail=json.dumps({"dueTime": arrow.get(due_time).to('local').replace(microsecond=0).isoformat() if due_time else None}, ensure_ascii=False),
            createTime=arrow.get(create_time).to('local').replace(microsecond=0).isoformat(),
        )
        cron_conn.insert({
            "create_time": time_now.datetime,
            "name": "call",
            "ref_id": str(call["_id"])
        })
