#! /usr/bin/env python
# coding: utf-8
import logging
import traceback
from functools import wraps

import arrow
import requests
import tornado.ioloop
from pymongo import MongoClient
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.common_util.mail import send_mail
from tools_lib.gmongoengine.config import MONGODB_CONFIG
from tools_lib.host_info import IP_PORT_API, DEBUG

mongo_client = MongoClient(**MONGODB_CONFIG)
TIME_PATTERN = '%Y-%m-%d %H:%M:%S'

if DEBUG:
    man_list = [
        "13245678901",
    ]

    leader_list = [
        "15258853865",
        "15695714288",
        "15558085328",
        "15189490872",
        "18458120857",
        "15962871675",
    ]

    driver_list = [
        "13245678901",
        "13245678902",
    ]
    mail_list = ["zhangjun@123feng.com"]

else:

    man_list = [
        # 全职配送员
        "15267138109",
        "15700121526",
        "18072722117",
        "18018333715",
        "15700184287",
        "18658171707",
        "18855158584",
        "15599044448",
        "15256443017",
        "15967178481",
        "13738026056",
        "13777352290",
        "18072947659",
        "18792426679",
        "18858271652",
        "18305818044",
        # 小队长
        "15258853865",
        "15695714288",
        "15558085328",
        "15189490872",
        "18458120857",
        "15962871675",
    ]

    leader_list = [
        "15258853865",
        "15695714288",
        "15558085328",
        "15189490872",
        "18458120857",
        "15962871675",
    ]

    driver_list = [
        "13082823376",
        "13575498576",
        "13575499831",
        "13588113114",
        "13735469767",
        "15345820012",
        "15381124468",
        "15557166936",
        "15700120622",
        "15805716681",
        "15869009193",
        "15869044298",
        "15924163456",
        "15990117619",
        "17767256212",
        "18218711837",
        "18657153719",
        "18668760225",
        "18756236888",
        "18758888361",
        "18868756003",
        "18895643469",
    ]
    mail_list = ["zhangjun@123feng.com", "zhuminmin123@dingtalk.com", "yuqi@123feng.com", "lanyina@123feng.com",
                 "yefei1017@dingtalk.com", "ygj0361@dingtalk.com", "caiguosong@dingtalk.com", "ygj0361@dingtalk.com"]

DRIVER_BASE = 135


def format_man(man_info, m_type='parttime'):
    man = dict()
    man['id'] = str(man_info['_id'])
    man['tel'] = man_info['tel']
    man['name'] = man_info.get('name', '')
    man['m_type'] = m_type
    return man


def get_zj_statistics(start_date, end_date):
    url = IP_PORT_API + "/shop/flow/complex_query"
    query = {
        "filter_col": ["shop_id", "type", "sum(cash) as total", "create_time"],
        "query":
            {
                "op": "AND",
                "exprs": [
                    {"create_time": {">=": TimeZone.date_to_str(start_date), "<": TimeZone.date_to_str(end_date)}},
                    {"type": {"in": ["TOP_UP", "PAY"]}},
                    {"is_not": 1, "shop_name": {"like": "%测试%"}}
                ]
            },
        "group_by": "shop_id,type",
        "count": 3000
    }

    resp = requests.post(url, json=query)
    if resp.status_code != 200:
        return 0, 0
    top_up = 0
    pay = 0
    for item in resp.json():
        print item
        if item['type'] == "PAY":
            pay += float(item['total'])
        elif item['type'] == "TOP_UP":
            top_up += float(item['total'])

    return top_up, pay


def once(name, days=-1):
    crontab_conn = mongo_client['aeolus']['crontab']

    def _once(func):
        @wraps(func)
        def _func():

            local = arrow.now().replace(days=days)
            # 如果今天运行过了, 就不要了再来一次了
            run_over = crontab_conn.find_one({
                "name": name,
                "create_time": {
                    "$gte": local.floor("day").datetime,
                    "$lte": local.ceil("day").datetime
                }
            })

            if run_over:
                return

            success = func()

            if success:
                crontab_conn.insert({"name": name, "create_time": local.datetime})

        return _func

    return _once


# 产生下一次运行的时间
def generate_next_time(when, func_name):
    """获得下一次运行的时间"""
    arrow_now = arrow.now()
    if arrow_now < arrow_now.replace(hour=when[0], minute=when[1]):
        ret = arrow_now.replace(hour=when[0], minute=when[1], second=0)
    else:
        ret = arrow_now.replace(days=+1, hour=when[0], minute=when[1], second=0)
    logging.info("Task named [{func_name}] scheduled at {time}".format(func_name=func_name, time=ret.format()))
    return ret.timestamp


# 确保业务能够在每次 callback 执行完之后计划下一次 callback 的时间
def call_at_day(func, when, mail_alert_to=("fangkai@123feng.com", "chenxinlu@123feng.com"), params=None):
    """
    :param func: 需要定时调用的函数
    :param when: 调用时间(HH, MM)
    :param mail_alert_to: 调用的过程中任何 exception 发邮件通知以下的人
    :param params: 传给该函数的参数, dict
    """
    if not params:
        params = {}

    def inner():
        try:
            # schedule next time to callback
            inst = tornado.ioloop.IOLoop.instance()
            inst.call_at(generate_next_time(when, func_name=func.func_name), inner)
            ret = func(**params)
            return ret
        except:
            s = traceback.format_exc()
            logging.error(s)
            send_mail(
                to_addrs=mail_alert_to,
                title="Crontab Exception: [{task_name}] [{datetime}]".format(
                    task_name=func.func_name,
                    datetime=arrow.now().format("YYYY-MM-DD HH:mm:ss")
                ),
                body=s
            )

    # schedule the first callback
    inst = tornado.ioloop.IOLoop.instance()
    inst.call_at(generate_next_time(when, func_name=func.func_name), inner)


if __name__ == '__main__':
    print get_zj_statistics()
