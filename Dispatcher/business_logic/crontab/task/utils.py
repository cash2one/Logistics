#! /usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals
import logging
import traceback
from functools import wraps

import arrow
import requests
import tornado.ioloop
from pymongo import MongoClient
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.common_util.mail import send_mail
from tools_lib.gmongoengine.config import PROD_MONGODB_CONFIG, MONGODB_CONFIG
from tools_lib.host_info import IP_PORT_API, DEBUG

# == 一些全局变量 ==
mongodb_client = MongoClient(**MONGODB_CONFIG)
cron_conn = mongodb_client['aeolus']['crontab']
expr_conn = mongodb_client['aeolus']['express']
call_conn = mongodb_client['aeolus']['call']

io_loop = tornado.ioloop.IOLoop.current()

TIME_PATTERN = '%Y-%m-%d %H:%M:%S'

mail_alert_to = ("fangkai@123feng.com", "chenxinlu@123feng.com")

if DEBUG:
    man_list = [
    ]

    leader_list = [
    ]

    driver_list = [
    ]
    mail_list = ["zhangjun@123feng.com"]

else:

    man_list = [
    ]

    leader_list = [
    ]

    driver_list = [
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
        if item['type'] == "PAY":
            pay += float(item['total'])
        elif item['type'] == "TOP_UP":
            top_up += float(item['total'])

    return top_up, pay


class Once(object):
    def __init__(self, name):
        self.now = arrow.now()
        self.name = name

    def __enter__(self):
        name = self.name
        now = self.now
        # 如果今天运行过了, 就不要了再来一次了
        ran = cron_conn.find_one({
            "name": name,
            "create_time": {
                "$gte": now.floor("day").datetime,
                "$lte": now.ceil("day").datetime
            }
        })
        if ran:
            logging.info("[{func_name}] 在 [{time}] 已运行过.".format(func_name=name, time=now.date()))
            return True
        else:
            # 今天还没有跑过呢: 跑咯
            logging.info("运行 [{time}] 的 [{func_name}]...".format(func_name=name, time=now.date()))
            return False

    def __exit__(self, type, value, traceback):
        name = self.name
        now = self.now
        cron_conn.insert({"name": name, "create_time": now.datetime})
        logging.info("运行 [{time}] 的 [{func_name}] 成功!".format(func_name=name, time=now.date()))


# 默认days=-1表示昨天
def once(name, days=0):
    def _once(func):
        @wraps(func)
        def _func():

            local = arrow.now().replace(days=days)
            # 如果今天运行过了, 就不要了再来一次了
            run_over = cron_conn.find_one({
                "name": name,
                "create_time": {
                    "$gte": local.floor("day").datetime,
                    "$lte": local.ceil("day").datetime
                }
            })

            if run_over:
                logging.info("[{func_name}] 在 [{time}] 已运行过.".format(func_name=name, time=local.date()))
                return
            else:
                # 今天还没有跑过呢: 跑咯
                cron_conn.insert({"name": name, "create_time": local.datetime})
                try:
                    logging.info("运行 [{time}] 的 [{func_name}]...".format(func_name=name, time=local.date()))
                    func(days)
                except Exception as e:
                    logging.exception(e)
                else:
                    logging.info("运行 [{time}] 的 [{func_name}] 成功!".format(func_name=name, time=local.date()))

        return _func

    return _once


# 产生下一次运行的时间
def generate_next_time(when):
    """获得下一次运行的时间"""
    arrow_now = arrow.now()
    # 发现今天还没到配置的运行时刻, 第一次跑的时间是今天
    if arrow_now < arrow_now.replace(hour=when[0], minute=when[1]):
        ret = arrow_now.replace(hour=when[0], minute=when[1], second=0)
    # 今天已经过了这个时间了, 第一次跑的时间是明天这个时刻
    else:
        # ret = arrow_now.replace(days=0, hour=when[0], minute=when[1], seconds=+10)
        ret = arrow_now.replace(days=+1, hour=when[0], minute=when[1], second=0)
    return ret.timestamp


def inner(func, when, params):
    try:
        # 真正的做事
        ret = func(**params)
        # 计算下次定时调用的时间
        next_when = generate_next_time(when)
        # 调度下次定时调用
        io_loop.call_at(next_when, inner, **{'func': func, 'when': when, 'params': params})
        logging.info("Task named [{func_name}] scheduled at [{time}]".format(
            func_name=func.func_name, time=arrow.get(next_when).to('local').isoformat()))
        return ret
    except Exception as e:
        s = traceback.format_exc()
        logging.exception(e)
        send_mail(
            to_addrs=mail_alert_to,
            title="Cron Exception: [{task_name}] [{datetime}]".format(
                task_name=func.func_name,
                datetime=arrow.now().isoformat()
            ),
            body=s
        )
        return None


# 确保业务能够在每次 callback 执行完之后计划下一次 callback 的时间
def call_at_day(func, when, params=None):
    """
    :param func: 需要定时调用的函数
    :param when: 调用时间(HH, MM)
    :param mail_alert_to: 调用的过程中任何 exception 发邮件通知以下的人
    :param params: 传给该函数的参数, dict
    """
    if not params:
        kwargs = {'func': func, 'when': when, 'params': {}}

    # 触发首次callback
    first_when = generate_next_time(when)
    io_loop.call_at(first_when, inner, **kwargs)
    logging.info("Task named [{func_name}] firstly scheduled at [{time}]".format(
        func_name=func.func_name, time=arrow.get(first_when).to('local').isoformat()))


if __name__ == '__main__':
    print(get_zj_statistics('', ''))
