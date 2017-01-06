#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals
import logging
import arrow
from utils import once, expr_conn, mongodb_client, send_mail
from tools_lib.bl_expr import ExprState


@once('发妥投率总结邮件', days=0)
def send_tt_summary(days=0):
    # with Once('发妥投率总结邮件') as done:
    #     if done:
    #         return
    r = {
        'title': '妥投率简报',

        'expr_count': 0,
        'from_real_client': 0,
        'from_testing': 0,

        'tt_count': 0,
        'tt_from_real_client': 0,
        'tt_from_testing': 0,

        'tt_rate': 0.0,
        'tt_rate_from_real_client': 0.0,
        'tt_rate_from_testing': 0.0,

        '时效 <4h': 0,
        '时效 4h-6h': 0,
        '时效 6h-8h': 0,
        '时效 >8h': 0,
    }
    start_time, end_time = arrow.now().replace(days=days).span('day')
    s, e = start_time.datetime, end_time.datetime
    day = start_time.date().isoformat()
    r['title'] = '%s妥投率简报' % day
    logging.info('开始计算[%s]妥投率...' % day)

    # 运单总量
    r['expr_count'] = expr_conn.find({
        "create_time": {"$gte": s, "$lte": e},
        'status.sub_status': {'$ne': ExprState.SUB_STATUS_CANCEL}
    }).count()
    logging.info('运单总量: %s' % r['expr_count'])
    # 1.2 演习 订单量
    r['from_testing'] = expr_conn.find({
        "create_time": {"$gte": s, "$lte": e},
        'creator.m_type': {'$in': ['test', 'test_map', 'test_task']},
        'status.sub_status': {'$ne': ExprState.SUB_STATUS_CANCEL}
    }).count()
    logging.info('演习 订单量: %s' % r['from_testing'])
    # 1.1 真实客户订单量
    r['from_real_client'] = r['expr_count'] - r['from_testing']
    logging.info('真实客户订单量: %s' % r['from_real_client'])

    # 妥投单量
    r['tt_count'] = expr_conn.find({
        "create_time": {"$gte": s, "$lte": e},
        "status.sub_status": ExprState.SUB_STATUS_FINISHED
    }).count()
    logging.info('妥投单量: %s' % r['tt_count'])
    # 2.1 演习订单妥投单量
    r['tt_from_testing'] = expr_conn.find({
        'create_time': {'$gte': s, '$lte': e},
        'status.sub_status': ExprState.SUB_STATUS_FINISHED,
        'creator.m_type': {'$in': ['test', 'test_map', 'test_task']}
    }).count()
    logging.info('演习订单妥投单量: %s' % r['tt_from_testing'])
    # 2.2 真实客户妥投单量
    r['tt_from_real_client'] = r['tt_count'] - r['tt_from_testing']
    logging.info('真实客户妥投单量: %s' % r['tt_from_real_client'])

    # 总妥投率
    if r['expr_count'] != 0:
        r['tt_rate'] = round(float(r['tt_count']) / r['expr_count'], 3)
    # 真实订单妥投率
    if r['from_real_client'] != 0:
        r['tt_rate_from_real_client'] = round(float(r['tt_from_real_client']) / r['from_real_client'],
                                              3)
    # 演习订单妥投率
    if r['from_testing'] != 0:
        r['tt_rate_from_testing'] = round(float(r['tt_from_testing']) / r['from_testing'], 3)

    # 时效
    if r['tt_count'] != 0:
        four = 1000 * 3600 * 4
        six = 1000 * 3600 * 6
        eight = 1000 * 3600 * 8
        time_limit_cursor = expr_conn.aggregate(
            [
                {
                    '$match': {
                        'create_time': {'$gte': s, '$lte': e},
                        'status.sub_status': ExprState.SUB_STATUS_FINISHED
                    }
                },
                {
                    '$project': {
                        '_id': 0,
                        # 'number': 1,
                        'is_less_than_4h': {
                            '$cond':
                                [
                                    {'$lte': [{'$subtract': ["$update_time", "$create_time"]}, four]},
                                    1,
                                    0
                                ]

                        },
                        'is_in_4h_6h': {
                            '$cond':
                                [
                                    {
                                        '$and': [
                                            {'$gt': [{'$subtract': ["$update_time", "$create_time"]}, four]},
                                            {'$lte': [{'$subtract': ["$update_time", "$create_time"]}, six]}
                                        ]
                                    },
                                    1,
                                    0
                                ]
                        },
                        'is_in_6h_8h': {
                            '$cond':
                                [
                                    {
                                        '$and': [
                                            {'$gt': [{'$subtract': ["$update_time", "$create_time"]}, six]},
                                            {'$lte': [{'$subtract': ["$update_time", "$create_time"]}, eight]}
                                        ]
                                    },
                                    1,
                                    0
                                ]
                        },
                        'is_more_than_8h': {
                            '$cond':
                                [
                                    {
                                        '$gt': [{'$subtract': ["$update_time", "$create_time"]}, eight]
                                    },
                                    1,
                                    0
                                ]
                        }
                    }
                }
                ,
                {
                    '$group': {
                        '_id': 0,
                        'less_than_4h': {'$sum': '$is_less_than_4h'},
                        '4h_6h': {'$sum': '$is_in_4h_6h'},
                        '6h_8h': {'$sum': '$is_in_6h_8h'},
                        'more_than_8h': {'$sum': '$is_more_than_8h'},
                    }
                }
            ])
        for doc in time_limit_cursor:
            # logging.info(doc.values())
            # 小于4h	妥投
            less_than_4h = doc['less_than_4h']
            logging.info('小于4h内妥投: %d/%s' % (less_than_4h, r['tt_count']))
            # less_than_4h = round(float(less_than_4h) / summary['tt_count'], 3)
            r['时效 <4h'] = less_than_4h

            # 4h-6h
            in_4h_6h = doc['4h_6h']
            logging.info('4h-6h内妥投: %d/%s' % (in_4h_6h, r['tt_count']))
            # in_4h_6h = round(float(in_4h_6h) / summary['tt_count'], 3)
            r['时效 4h-6h'] = in_4h_6h

            # 6h-8h
            in_6h_8h = doc['6h_8h']
            logging.info('6h-8h内妥投: %d/%s' % (in_6h_8h, r['tt_count']))
            # in_6h_8h = round(float(in_6h_8h) / summary['tt_count'], 3)
            r['时效 6h-8h'] = in_6h_8h

            # 8h以上
            more_than_8h = doc['more_than_8h']
            logging.info('大于8h内妥投: %d/%s' % (more_than_8h, r['tt_count']))
            # more_than_8h = round(float(more_than_8h) / summary['tt_count'], 3)
            r['时效 >8h'] = more_than_8h
            break
    # logging.info(json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True))

    # 生成html
    title = r['title']
    tt = r['tt_count']
    body = """
        <html>
        <style type="text/css">
        .tg  {border-collapse:collapse;border-spacing:0;border-color:#ccc;}
        .tg td{font-family:Arial, sans-serif;font-size:14px;padding:5px 12px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;border-color:#ccc;color:#333;background-color:#fff;border-top-width:1px;border-bottom-width:1px;}
        .tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:5px 12px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;border-color:#ccc;color:#333;background-color:#f0f0f0;border-top-width:1px;border-bottom-width:1px;}
        .tg .tg-e63f{background-color:#f9f9f9;font-size:13px;font-family:"Times New Roman", Times, serif !important;;vertical-align:top}
        .tg .tg-smzr{font-family:"Times New Roman", Times, serif !important;;vertical-align:top}
        .tg .tg-lmdf{font-size:12px;font-family:"Times New Roman", Times, serif !important;;vertical-align:top}
        </style>
        <table class="tg">
          <tr>
            <th class="tg-smzr" colspan="3">%s</th>
          </tr>
          <tr>
            <td class="tg-smzr">运单总量</td>
            <td class="tg-e63f">%d</td>
            <td class="tg-lmdf"></td>
          </tr>
          <tr>
            <td class="tg-smzr">演习 订单量</td>
            <td class="tg-e63f">%d</td>
            <td class="tg-lmdf"></td>
          </tr>
          <tr>
            <td class="tg-smzr">真实客户订单量</td>
            <td class="tg-e63f">%d</td>
            <td class="tg-lmdf"></td>
          </tr>
          <tr>
            <td class="tg-smzr"></td>
            <td class="tg-e63f"></td>
            <td class="tg-lmdf"></td>
          </tr>
          <tr>
            <td class="tg-smzr">妥投单量</td>
            <td class="tg-e63f">%d/%d</td>
            <td class="tg-lmdf" style="color: #c00;">%.1f%%</td>
          </tr>
          <tr>
            <td class="tg-smzr">演习订单妥投单量</td>
            <td class="tg-e63f">%d/%d</td>
            <td class="tg-lmdf">%.1f%%</td>
          </tr>
          <tr>
            <td class="tg-smzr">真实客户妥投单量</td>
            <td class="tg-e63f">%d/%d</td>
            <td class="tg-lmdf">%.1f%%</td>
          </tr>
          <tr>
            <td class="tg-smzr"></td>
            <td class="tg-e63f"></td>
            <td class="tg-lmdf"></td>
          </tr>
          <tr>
            <td class="tg-smzr">小于4h内妥投</td>
            <td class="tg-e63f">%d/%d</td>
            <td class="tg-lmdf">%.1f%%</td>
          </tr>
          <tr>
            <td class="tg-smzr">4h-6h内妥投</td>
            <td class="tg-e63f">%d/%d</td>
            <td class="tg-lmdf">%.1f%%</td>
          </tr>
          <tr>
            <td class="tg-smzr">6h-8h内妥投</td>
            <td class="tg-e63f">%d/%d</td>
            <td class="tg-lmdf">%.1f%%</td>
          </tr>
          <tr>
            <td class="tg-smzr">大于8h内妥投</td>
            <td class="tg-e63f">%d/%d</td>
            <td class="tg-lmdf">%.1f%%</td>
          </tr>
        </table>
        </html>""" % (
        title,
        # 运单总量, 演习 订单量, 真实客户订单量
        r['expr_count'], r['from_testing'], r['from_real_client'],
        # 妥投单量
        r['tt_count'], r['expr_count'], r['tt_rate'] * 100,
        # 演习订单妥投单量
        r['tt_from_testing'], r['from_testing'], r['tt_rate_from_testing'] * 100,
        # 真实客户妥投单量
        r['tt_from_real_client'], r['from_real_client'], r['tt_rate_from_real_client'] * 100,
        # 小于4h内妥投
        r['时效 <4h'], tt, 0.0 if tt == 0 else r['时效 <4h'] / float(tt) * 100,
        # 4h-6h内妥投
        r['时效 4h-6h'], tt, 0.0 if tt == 0 else r['时效 4h-6h'] / float(tt) * 100,
        # 6h-8h内妥投
        r['时效 6h-8h'], tt, 0.0 if tt == 0 else r['时效 6h-8h'] / float(tt) * 100,
        # 大于8h内妥投
        r['时效 >8h'], tt, 0.0 if tt == 0 else r['时效 >8h'] / float(tt) * 100
    )
    # print(body)
    to = ['songxueting@123feng.com', 'laikeyi@123feng.com', 'yuqi@123feng.com', 'tianxi@123feng.com',
          'wangsong@123feng.com', 'chenxinlu@123feng.com']
    for t in to:
        send_mail(t, title, body, 'html')
    # send_mail(['chenxinlu@123feng.com'], title, body, 'html')
    return True


if __name__ == "__main__":
    import sys
    import os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
    logging.root.level = logging.INFO

    send_tt_summary()
    mongodb_client.close()
