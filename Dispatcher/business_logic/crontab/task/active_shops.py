#!/usr/bin/env python
# coding:utf-8
"""
活跃客户数的定义: 最近7日内，发件大于等于4天的客户
"""

import json
import arrow
import logging
from .utils import once, expr_conn, mongodb_client, send_mail
from tools_lib.bl_expr import ExprState


@once('活跃客户数简报', days=0)
def send_active_shops_summary(days=0):
    end_time, start_time = arrow.now().replace(days=days + 1).span('day', count=-7)
    s, e = start_time.datetime, end_time.datetime
    logging.info('开始计算[%s]活跃客户数...' % e)

    active_shops_cursor = expr_conn.aggregate(
        [
            # 过去7天内的单
            {
                '$match': {
                    'create_time': {'$gte': s, '$lte': e}
                }
            },
            # 按照[商户, 日期]分类
            {
                '$group': {
                    "_id": {
                        "creator_id": "$creator.id",
                        "creator_name": "$creator.name",
                        "creator_tel": "$creator.tel",
                        "day": {"$dayOfMonth": {"$add": ['$create_time', 28800000]}},  # 要加8小时哟
                    },
                    # 'creator': {'$first': '$creator'},
                    'count': {'$sum': 1}
                }
            }
        ]
    )

    creator_days = {}  # {creator_id: {id:, name:, tel, days=set(1,2,3,28,29,30,31)}
    for doc in active_shops_cursor:
        # logging.info(doc.values())
        _id = doc['_id']
        creator_id, name, tel, day = _id['creator_id'], _id['creator_name'], _id['creator_tel'], _id['day']
        # if creator_id not in creator_days:
        #     creator_days[creator_id] = {
        #         'id': creator_id,
        #         'name': name,
        #         'tel': tel,
        #         'days': {day}
        #     }
        # else:
        #     creator_days[creator_id]['days'].add(day)
        if tel not in creator_days:
            creator_days[tel] = {day}
        else:
            creator_days[tel].add(day)

    a = {}
    for k, v in list(creator_days.items()):
        if len(v) >= 4:
            a[k] = len(v)
    # print(json.dumps(a, ensure_ascii=False, indent=2))
    logging.info('客户数量为: %s' % len(a))

    # 邮件发送
    day_in_title = arrow.now().replace(days=days).date().isoformat()
    html = """
        <style type="text/css">
        .tg  {border-collapse:collapse;border-spacing:0;border-color:#ccc;}
        .tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;border-color:#ccc;color:#333;background-color:#fff;border-top-width:1px;border-bottom-width:1px;}
        .tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;border-color:#ccc;color:#333;background-color:#f0f0f0;border-top-width:1px;border-bottom-width:1px;}
        .tg .tg-baqh{text-align:center;vertical-align:top}
        .tg .tg-dzk6{background-color:#f9f9f9;text-align:center;vertical-align:top}
        </style>
        <table id="tg-t5V7w" class="tg">
          <tr>
            <th class="tg-yw4l">日期</th>
            <th class="tg-yw4l">活跃客户数量</th>
          </tr>
          <tr>
            <td class="tg-baqh">%s</td>
            <td class="tg-dzk6">%s</td>
          </tr>
        </table>
        """ % (day_in_title, len(a))
    # for to_addr in ['fangkai@123feng.com', 'chenxinlu@123feng.com']:
    for to_addr in ['songxueting@123feng.com', 'tianxi@123feng.com', 'wangsong@123feng.com', 'chenxinlu@123feng.com']:
        send_mail(to_addr, '%s活跃客户数简报' % day_in_title, html, 'html')
    return len(a)


if __name__ == "__main__":
    from tools_lib.common_util.log import simple_conf_init

    simple_conf_init()
    # b = []
    # for i in range(-31, 0):
    #     which_day = arrow.now().replace(days=i).date().isoformat()
    #     count = send_active_shops_summary(days=i)
    #     b.append((which_day, count))
    # mongodb_client.close()
    #
    # tds = ""
    # for l in b:
    #     td = """
    #     <tr>
    #     <td class="tg-baqh">%s</td>
    #     <td class="tg-dzk6">%s</td>
    #     </tr>
    #     """ % (l[0], l[1])
    #     tds += td
    # html = """
    # <style type="text/css">
    # .tg  {border-collapse:collapse;border-spacing:0;border-color:#ccc;}
    # .tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;border-color:#ccc;color:#333;background-color:#fff;border-top-width:1px;border-bottom-width:1px;}
    # .tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;border-color:#ccc;color:#333;background-color:#f0f0f0;border-top-width:1px;border-bottom-width:1px;}
    # .tg .tg-baqh{text-align:center;vertical-align:top}
    # .tg .tg-dzk6{background-color:#f9f9f9;text-align:center;vertical-align:top}
    # </style>
    # <table id="tg-t5V7w" class="tg">
    #   <tr>
    #     <th class="tg-yw4l">日期</th>
    #     <th class="tg-yw4l">活跃客户数量</th>
    #   </tr>
    #   %s
    # </table>
    # """ % tds
    #
    # # print(html)
    # # to = ['songxueting@123feng.com', 'wangsong@123feng.com', 'chenxinlu@123feng.com']
    # to = ['chenxinlu@123feng.com']
    # send_mail(to, '10.1-10.31日活跃客户数简报', html, 'html')
    send_active_shops_summary(days=0)
    mongodb_client.close()
