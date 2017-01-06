#! /usr/bin/env python
# coding: utf-8
import logging
from datetime import datetime

import arrow
from models import Settlement, Rewards
from tools_lib.common_util.sstring import safe_join
from tools_lib.host_info import DEBUG
from utils import man_list, leader_list, driver_list
from utils import mongodb_client, format_man, DRIVER_BASE

if DEBUG:
    _start_arrow = arrow.get(datetime(2016, 5, 30), "local")
else:
    _start_arrow = arrow.get(datetime(2016, 6, 1), "local")


def get_man_base(tel):
    if tel in leader_list:
        return 100
    elif tel in man_list:
        return 80

    return 0


def parttime_settlement():
    logging.info("parttime_settlement start...")
    man_conn = mongodb_client['profile']['man']
    express = mongodb_client['aeolus']['express']

    m_type = "parttime"

    log = []
    settlements = []

    for man_info in man_conn.find({"job_description": m_type}):
        man = format_man(man_info, m_type)

        if man['tel'] not in man_list:
            continue

        settlement = Settlement.objects(man__id=man['id'], man__m_type=m_type).first()
        start_date = _start_arrow.datetime
        if settlement:
            # 如果有数据,则从数据的后一天开始算
            start_date = arrow.get(settlement.create_time, "utc").replace(days=1).to("local").datetime

        # 最多计算到昨天
        end_date = arrow.now().replace(days=-1).datetime
        # 从开始日期开始到昨天都需要计算

        for day in arrow.Arrow.range("day", start_date, end_date):
            start_time, end_time = day.span("day")
            start_time = start_time.datetime
            end_time = end_time.datetime
            # 收件提成
            result = express.aggregate([
                {
                    "$match": {
                        "watchers.0.id": man['id'],
                        "watchers.0.m_type": man['m_type'],
                        "times.sj_time": {
                            "$gte": start_time,
                            "$lte": end_time
                        },
                        "times.zj_time": {"$exists": True},
                        "fee.sj_profit": {"$exists": True},
                    }
                },
                {
                    "$group": {
                        "_id": "sum",
                        "profit": {"$sum": "$fee.sj_profit"}
                    }

                }
            ])

            result = list(result)
            sj_profit = 0
            if result:
                sj_profit = result[0]['profit']

            # 派件提成
            result = express.aggregate([
                {
                    "$match": {
                        "assignee.id": man['id'],
                        "assignee.m_type": man['m_type'],
                        "times.parttime_tt_time": {
                            "$gte": start_time,
                            "$lte": end_time
                        },
                        "fee.pj_profit": {"$exists": True},
                    }
                },
                {
                    "$group": {
                        "_id": "",
                        "profit": {"$sum": "$fee.pj_profit"}
                    }

                }
            ])

            result = list(result)
            pj_profit = 0
            if result:
                pj_profit = result[0]['profit']

            # 先将时间加上本地tzinfo, 然后再转换时区, 直接指定tzinfo会出错, 差6分钟, 故意躲加1小时
            create_time = day.floor("day").replace(hours=1).to("utc").datetime
            reward = Rewards.objects(
                man__id=man['id'],
                man__m_type=man['m_type'],
                create_time__gte=start_time,
                create_time__lte=end_time,
                money__gt=0
            ).aggregate_sum("money")

            punishment = Rewards.objects(
                man__id=man['id'],
                man__m_type=man['m_type'],
                create_time__gte=start_time,
                create_time__lte=end_time,
                money__lt=0
            ).aggregate_sum("money")

            # 如果今天的分成为0, 则说明没有手牌
            if sj_profit + pj_profit > 0:
                base = get_man_base(man['tel'])
            else:
                base = 0

            insurance = 0
            total = base + insurance + reward + punishment + sj_profit + pj_profit

            log.append([m_type, day, man['tel'], man['name'], sj_profit, pj_profit, reward, punishment])

            settlements.append(Settlement(
                man=man,
                sj_profit=sj_profit,
                pj_profit=pj_profit,
                base=base,
                insurance=insurance,
                reward=reward,
                punishment=punishment,
                total=total,
                create_time=create_time
            ))
    # =============================================

    for _ in settlements:
        _.save()

    for _ in log:
        logging.info(safe_join(_, ", "))

    logging.info("parttime_settlement end...")


def driver_settlement():
    logging.info("driver_settlement start...")
    man_conn = mongodb_client['profile']['man']

    m_type = "city_driver"
    log = []
    settlements = []

    for man_info in man_conn.find({"job_description": m_type}):
        man = format_man(man_info, m_type)

        if man['tel'] not in driver_list:
            continue

        settlement = Settlement.objects(man__id=man['id'], man__m_type=m_type).order_by("-create_time").first()
        start_date = _start_arrow.datetime
        if settlement:
            # 如果有数据,则从数据的后一天开始算
            start_date = arrow.get(settlement.create_time, "utc").replace(days=1).to("local").datetime

        # 最多计算到昨天
        end_date = arrow.now().replace(days=-1).datetime
        # 从开始日期开始到昨天都需要计算

        for day in arrow.Arrow.range("day", start_date, end_date):
            start_time, end_time = day.span("day")
            start_time = start_time.datetime
            end_time = end_time.datetime

            reward = Rewards.objects(
                man__id=man['id'],
                man__m_type=man['m_type'],
                create_time__gte=start_time,
                create_time__lte=end_time,
                money__gt=0
            ).aggregate_sum("money")

            punishment = Rewards.objects(
                man__id=man['id'],
                man__m_type=man['m_type'],
                create_time__gte=start_time,
                create_time__lte=end_time,
                money__lt=0
            ).aggregate_sum("money")

            # 先将时间加上本地tzinfo, 然后再转换时区, 直接指定tzinfo会出错, 差6分钟, 故意多加1小时
            create_time = day.floor("day").replace(hours=1).to("utc").datetime

            insurance = 0
            total = DRIVER_BASE + insurance + reward + punishment

            log.append([m_type, day, man['tel'], man['name'], reward, punishment])
            settlements.append(Settlement(
                man=man,
                base=DRIVER_BASE,
                insurance=insurance,
                reward=reward,
                punishment=punishment,
                total=total,
                create_time=create_time
            ))

    # =============================================

    for _ in settlements:
        _.save()

    for _ in log:
        logging.info(safe_join(_, ", "))

    logging.info("driver_settlement end...")


def insurance_monthly():
    local = arrow.now()
    if local.day != 1:
        return

    logging.info("insurance_monthly start...")
    start_time, end_time = local.replace(months=-1).span("month")
    start_time = start_time.datetime
    end_time = end_time.datetime
    m_type = "parttime"
    result = Settlement.objects(man__m_type=m_type, create_time__gte=start_time, create_time__lte=end_time).aggregate(
        {
            "$group": {
                "_id": {
                    "year": {"$year": {"$add": ['$create_time', 28800000]}},
                    "month": {"$month": {"$add": ['$create_time', 28800000]}},
                    "day": {"$dayOfMonth": {"$add": ['$create_time', 28800000]}},
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {
                "_id.day": 1
            }
        }
    )

    result = list(result)
    msg = "\n日期\t人数\n"
    for doc in result:
        msg += "%s-%s-%s\t%s\n" % (doc['_id']['year'], doc['_id']['month'], doc['_id']['day'], doc['count'])

    logging.info(msg)
    logging.info("insurance_monthly end...")
