#! /usr/bin/env python
# coding: utf-8
import logging
from datetime import datetime

import pytz
from .models import Rewards
from tools_lib.common_util.archived.gtz import TimeZone
from tornado.escape import utf8
from .utils import mongodb_client, format_man


def shop_reward():
    logging.info("invitation shop reward start...")
    man_conn = mongodb_client['profile']['man']
    shop_conn = mongodb_client['profile']['shop']
    express = mongodb_client['aeolus']['express']

    now = TimeZone.utc_now()
    local = TimeZone.local_now()
    cursor = shop_conn.find(
        {"recommended_by.tel": {"$exists": True}, "recommended_by.time": {"$gt": TimeZone.decrement_months(now, 2)}}
    )

    m_type = "shop_invitation"
    for doc in cursor:
        man = man_conn.find_one({"tel": doc['recommended_by']['tel']})
        if not man:
            logging.warning("no man tel:%s", doc['recommended_by']['tel'])
            continue

        shop_id = str(doc['_id'])
        shop_name = utf8(doc.get("name", "新客户"))
        man = format_man(man, 'parttime')
        invite_time = TimeZone.naive_to_aware(doc['recommended_by']['time'], pytz.utc)

        # 拿出这个人对应商户所有的奖励, 用来计算已经奖励了多少钱
        reward_list = Rewards.objects(man__id=man['id'], source__shop_id=shop_id, m_type=m_type)

        # 计算还剩多少可以奖励
        count = 0
        for r in reward_list:
            count += r.money
        count = int(count)
        left = 100 - count

        # 如果没剩了, 不能再奖励了
        if left <= 0:
            continue
        # 计算最近一次需要计算的日期,
        try:
            reward = reward_list[0]
            start_date = TimeZone.utc_to_local(TimeZone.increment_days(reward.create_time, 1)).date()

        except IndexError:
            start_date = TimeZone.utc_to_local(invite_time).date()
        # 最多计算到昨天
        end_date = local.date()

        # 从开始日期开始到昨天都需要计算
        for day in TimeZone.date_xrange(start_date, end_date):
            start_time, end_time = TimeZone.day_range(value=day)
            # 限制一下start_time
            start_time = start_time if start_time > invite_time else invite_time

            _count = express.find({
                "creator.id": shop_id,
                "times.sj_time": {
                    "$gte": start_time,
                    "$lte": end_time
                },
            }).count()

            if _count == 0:
                continue

            c = _count if _count < left else left

            money = c * 1.0
            # 先将时间加上本地tzinfo, 然后再转换时区, 直接指定tzinfo会出错, 差6分钟, 故意躲加1小时
            create_time = TimeZone.datetime_to_utc(TimeZone.naive_to_aware(datetime(day.year, day.month, day.day, 1)))
            Rewards(
                m_type=m_type,
                title="邀请客户",
                desc="%s当日下单%s单" % (shop_name, c),
                man=man,
                money=money,
                source={
                    "shop_id": shop_id,
                    "shop_name": shop_name
                },
                create_time=create_time
            ).save()
            logging.info("reward: m_type[%s], date[%s], man[%s], shop_id[%s], money[%s]", m_type, day, man['id'],
                         shop_id, money)

            left -= c
            if left <= 0:
                break


def man_reward():
    logging.info("invitation man reward start...")
    man_conn = mongodb_client['profile']['man']
    express = mongodb_client['aeolus']['express']

    now = TimeZone.utc_now()
    local = TimeZone.local_now()
    cursor = man_conn.find(
        {"recommended_by.tel": {"$exists": True}, "recommended_by.time": {"$gt": TimeZone.decrement_months(now, 2)}}
    )

    m_type = "man_invitation"
    for doc in cursor:
        man = man_conn.find_one({"tel": doc['recommended_by']['tel']})
        if not man:
            logging.warning("no man tel:%s", doc['recommended_by']['tel'])
            continue

        man_id = str(doc['_id'])
        man_name = utf8(doc.get("name", "新风先生"))
        man = format_man(man, "parttime")
        invite_time = TimeZone.naive_to_aware(doc['recommended_by']['time'], pytz.utc)

        # 拿出这个人对应商户所有的奖励, 用来计算已经奖励了多少钱
        reward_list = Rewards.objects(man__id=man['id'], source__man_id=man_id, m_type=m_type)

        # 计算还剩多少可以奖励
        count = 0
        for r in reward_list:
            count += r.money
        count = int(count / 0.3)
        left = 100 - count

        # 如果没剩了, 不能再奖励了
        if left <= 0:
            continue
        # 计算最近一次需要计算的日期,
        try:
            reward = reward_list[0]
            start_date = TimeZone.utc_to_local(TimeZone.increment_days(reward.create_time, 1)).date()

        except IndexError:
            start_date = TimeZone.utc_to_local(invite_time).date()
        # 最多计算到昨天
        end_date = local.date()

        # 从开始日期开始到昨天都需要计算
        for day in TimeZone.date_xrange(start_date, end_date):
            start_time, end_time = TimeZone.day_range(value=day)
            # 限制一下start_time
            start_time = start_time if start_time > invite_time else invite_time

            _count = express.find({
                "watchers.0.id": man_id,
                "watchers.0.m_type": "parttime",
                "times.zj_time": {
                    "$gte": start_time,
                    "$lte": end_time
                },
            }).count()

            if _count == 0:
                continue

            c = _count if _count < left else left

            money = c * 0.3
            # 先将时间加上本地tzinfo, 然后再转换时区, 直接指定tzinfo会出错, 差6分钟, 故意躲加1小时
            create_time = TimeZone.datetime_to_utc(TimeZone.naive_to_aware(datetime(day.year, day.month, day.day, 1)))
            Rewards(
                m_type=m_type,
                title="推荐配送员",
                desc="%s有效收件%s单" % (man_name, c),
                man=man,
                money=money,
                source={
                    "man_id": man_id,
                    "man_name": man_name
                },
                create_time=create_time
            ).save()
            logging.info("reward: m_type[%s], date[%s], man[%s], from_man[%s], money[%s]", m_type, day, man['id'],
                         man_id, money)

            left -= c
            if left <= 0:
                break
