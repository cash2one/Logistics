#! /usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

import logging
from datetime import date, datetime

import arrow
import psycopg2
from models import OpData
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.host_info import CONFIG_POSTGRESQL
from utils import mongodb_client, get_zj_statistics, driver_list, TIME_PATTERN


# def daily():
#     logging.info("data daily start...")
#     express = mongo_client['aeolus']['express']
#
#     start_time, end_time = arrow.now().span("day")
#     start_time = start_time.datetime
#     end_time = end_time.datetime
#
#     pre_created = express.find({
#         "status.status": "PRE_CREATED",
#         "creator.name": {"$regex": "^(?!.*测试.*)"},  # 不匹配测试开头的运单
#     }).count()
#
#     sending = express.find({
#         "status.status": "SENDING",
#         "creator.name": {"$regex": "^(?!.*测试.*)"},  # 不匹配测试开头的运单
#     }).count()
#
#     finished = express.find({
#         "status.sub_status": "FINISHED",
#         "creator.name": {"$regex": "^(?!.*测试.*)"},  # 不匹配测试开头的运单
#         "times.parttime_tt_time": {
#             "$gte": start_time,
#             "$lte": end_time
#         }
#     }).count()
#
#     msg = """
#     ============== 运单数据 ============
#     待收件: %s
#     配送中: %s
#     今日已妥投: %s
#     ===================================
#     """ % (pre_created, sending, finished)
#
#     mail_list = [
#         "zhuminmin@123feng.com, yuguojun@123feng.com, liuda@123feng.com"
#     ]
#     send_mail(mail_list, "全城运单数据", msg)
#     logging.info("data daily end...")


def op_data():
    logging.info("op_data start...")

    man_conn = mongodb_client['profile']['man']
    shop_conn = mongodb_client['profile']['shop']
    express = mongodb_client['aeolus']['express']

    opdata = OpData.objects.order_by("-create_time").first()

    start_date = date(2016, 5, 20)
    if opdata:
        start_date = TimeZone.increment_days(TimeZone.utc_to_local(opdata.create_time), 1).date()
    end_date = TimeZone.local_now().date()

    for day in TimeZone.date_xrange(start_date, end_date):
        start_time, end_time = TimeZone.day_range(value=day)

        logging.info("op data %s", day)
        data = {}
        # ============= 资金 ==============
        data['zj_top_up'], data['zj_pay'] = get_zj_statistics(day, TimeZone.increment_days(day))

        # ============= 订单 ==============
        data['dd_count'] = express.find({"create_time": {"$gte": start_time, "$lte": end_time}}).count()
        data['dd_sj_count'] = express.find({"times.zj_time": {"$gte": start_time, "$lte": end_time}}).count()
        data['dd_tt_count'] = express.find({"times.parttime_tt_time": {"$gte": start_time, "$lte": end_time}}).count()
        data['dd_error_count'] = express.find({"times.yc_time": {"$gte": start_time, "$lte": end_time}}).count()

        # ============= 客户 ==============
        data['sh_register'] = shop_conn.find({"create_time": {"$gte": start_time, "$lte": end_time}}).count()
        data['sh_order'] = 0
        result = express.aggregate([
            {"$match": {"create_time": {"$gte": start_time, "$lte": end_time}}},
            {"$group": {
                "_id": "$creator.id",
            }},
            {"$group": {
                "_id": "sum",
                "count": {"$sum": 1}
            }}
        ])
        for doc in result:
            data['sh_order'] += doc['count']

        # ============== 人力 ===============
        data['hr_on_job'] = man_conn.find({"job_description": "parttime", "status": "STATUS_WORKING"}).count()
        data['hr_active'] = 0
        # 在规定时间内收件的人
        result = express.aggregate([
            {
                "$match": {
                    "times.sj_time": {
                        "$gte": start_time, "$lte": end_time
                    }
                }
            },
            {
                "$project": {
                    "man": {"$arrayElemAt": ["$watchers", 0]}
                }
            },
            {
                "$group": {
                    "_id": "$man.id"
                }
            }
        ])
        active_list = [_['_id'] for _ in result]

        result = express.aggregate([
            {"$match": {"times.parttime_tt_time": {"$gte": start_time, "$lte": end_time}}},
            {"$group": {
                "_id": "$assignee.id",
            }}
        ])
        # 在规定时间内妥投的人
        active_list2 = [_['_id'] for _ in result]
        temp = set(active_list + active_list2)
        data['hr_active'] = len(temp)

        # 司机出勤
        man_list = man_conn.find({"tel": {"$in": driver_list}})
        node_conn = psycopg2.connect(cursor_factory=psycopg2.extras.DictCursor, database="tlbs", **CONFIG_POSTGRESQL)
        cursor = node_conn.cursor()
        data['cl_depart'] = 0
        man_id_list = [str(_['_id']) for _ in man_list]

        for man_id in man_id_list:
            local = arrow.get(day, "local")
            cursor.execute(
                """SELECT count(*)
                from trans.bs_trans_deliver_sign_record
                where deliver_id = %s and create_time >= %s and create_time <= %s
                """,
                (man_id, local.floor("day").strftime(TIME_PATTERN), local.ceil("day").strftime(TIME_PATTERN))
            )

            doc = cursor.fetchone()
            if doc and int(doc[0]) > 0:
                data['cl_depart'] += 1
        cursor.execute(
            """
            SELECT count(*)
            FROM trans.bs_trans_bind_node_info
            WHERE deliver_id = ANY(%s)
            """,
            (man_id_list,)
        )
        doc = cursor.fetchone()
        if not doc:
            data['cl_shift'] = 0
        else:
            data['cl_shift'] = int(doc[0])

        # =======================================
        create_time = TimeZone.datetime_to_utc(TimeZone.naive_to_aware(datetime(day.year, day.month, day.day, 1)))

        data["create_time"] = create_time
        OpData(**data).save()

    logging.info("op_data end...")
