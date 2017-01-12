#!/usr/bin/env python
# coding:utf-8

import os
import arrow
import logging
import pymongo
from .utils import expr_conn, TIME_PATTERN
from tools_lib.common_util.mail import send_mail
from tools_lib.common_util.xls import xls_writer


def expr_list():
    # 今天的单
    start, end = arrow.now().span('day')
    logging.info('开始查找 [%s] - [%s] 的运单...' % (start, end))
    query = {
        'create_time': {'$gte': start.datetime, '$lte': end.datetime}
    }
    qs = expr_conn.find(
        query,
        {'_id': 0, 'creator': 1, 'number': 1, 'create_time': 1}
    ).limit(1000).sort(
        [('creator.id', pymongo.ASCENDING),
         ('create_time', pymongo.ASCENDING)]
    )

    summary = [['订单ID', '客户ID', '客户名', '时间']]
    for e in qs:
        case = [e['number'], e['creator']['id'], e['creator']['name'], e['create_time'].strftime(TIME_PATTERN)]
        summary.append(case)

    # for i, c in enumerate(summary):
    #     print(i + 1, c)

    day = start.format('YYYY-MM-DD')
    fn = "%s.xls" % day
    xls_writer(summary).save(fn)
    with open(fn, "rb") as z:
        stream = z.read()
        mail_list = ['chenxinlu@123feng.com']
        send_mail(mail_list,
                  "%s客户运单明细" % day,
                  "这是线上服务器发出的线上数据\n数据日期: %s" % day,
                  content_type='plain',
                  file_name=fn,
                  file_stream=stream)
    os.remove(fn)


if __name__ == '__main__':
    from tools_lib.common_util.log import simple_conf_init

    simple_conf_init()

    expr_list()
