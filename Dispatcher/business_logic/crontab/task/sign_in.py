# ! /usr/bin/env python
# coding: utf-8


import json
import logging
from datetime import datetime

import arrow
import psycopg2
import psycopg2.extras
from .models import Rewards
from tools_lib.common_util.mail import send_mail
from tools_lib.common_util.sstring import safe_join
from tools_lib.common_util.xls import xls_writer
from tools_lib.geo.mercator import Mercator
from tools_lib.host_info import CONFIG_POSTGRESQL, DEBUG
from .utils import man_list, driver_list, mail_list, TIME_PATTERN
from .utils import mongodb_client, once, format_man, DRIVER_BASE

if DEBUG:
    punish_time = arrow.get(datetime(2016, 5, 1), 'local')
else:
    punish_time = arrow.get(datetime(2016, 6, 1), 'local')

MAX_DISTANCE = 1000


def man_find_first_valid_sign(data, lng, lat):
    if not data:
        return None

    for _ in data:
        loc = _['loc']
        distance = Mercator.distance(lng, lat, loc['lng'], loc['lat'])

        if distance < MAX_DISTANCE:
            return _
        continue
    return None


def driver_find_first_valid_sign(cursor, driver_id, start_time, end_time, lng, lat):
    cursor.execute(
        """
        SELECT deliver_id, ST_AsGeoJSON(loc), create_time
        FROM trans.bs_trans_deliver_sign_record
        WHERE deliver_id = %s and create_time >= %s and create_time <= %s
        ORDER BY create_time DESC
        """,
        (driver_id, start_time, end_time)
    )
    sign_list = cursor.fetchall()
    if not sign_list:
        return None

    for sign in sign_list:
        _, loc, create_time = sign
        _lng, _lat = json.loads(loc)['coordinates']
        distance = Mercator.distance(lng, lat, _lng, _lat)

        if distance < MAX_DISTANCE:
            return {
                "lng": _lng,
                "lat": _lat,
                "create_time": arrow.get(create_time, "local").datetime
            }

    return None


def find_man_node(cursor, deliver_id):
    # 配送员也会有很多店, 只需要8点30分的点
    cursor.execute(
        """
        select b.reg_cron, c.node_name, ST_AsGeoJSON(c.loc)
        from trans.bs_trans_bind_node_info as a, trans.bs_trans_reg_time as b, trans.bs_trans_node_info as c
        where a.deliver_id = %s and a.status = 1 and a.cron_id = b.id and b.reg_cron = '0 30 8 * * ?' and a.node_id = c.node_id
        order by a.create_time DESC;
        """,
        (deliver_id,)
    )
    node = cursor.fetchone()
    if not node:
        return None
    else:
        _, node_name, loc = node
        lng, lat = json.loads(loc)['coordinates']
        return [node_name, lng, lat]


def find_driver_node(cursor, deliver_id):
    # find node
    cursor.execute(
        """
        select b.reg_cron, c.node_name, ST_AsGeoJSON(c.loc)
        from trans.bs_trans_bind_node_info as a, trans.bs_trans_reg_time as b, trans.bs_trans_node_info as c
        where a.deliver_id = %s and a.status = 1 and a.cron_id = b.id and a.node_id = c.node_id
        order by a.create_time DESC;
        """,
        (deliver_id,)
    )
    node_list = cursor.fetchall()
    if not node_list:
        return None

    ret = []

    for node in node_list:
        reg_cron, node_name, loc = node
        lng, lat = json.loads(loc)['coordinates']

        temp = reg_cron.strip().split(" ")
        temp.pop(0)
        minute = int(temp.pop(0))
        hour = int(temp.pop(0))

        ret.append([node_name, lng, lat, hour, minute])

    return ret


@once("man_sign_in", days=0)
def man(days=0):
    # 派件员每天10点以后, 跑今天的数据

    local = arrow.now().replace(days=days)
    # 10点之后再运行
    if local.hour < 10:
        return False

    node_conn = psycopg2.connect(cursor_factory=psycopg2.extras.DictCursor, database="tlbs", **CONFIG_POSTGRESQL)
    # 初始化时间
    start = local.replace(hour=6, minute=30).floor("minute").datetime
    end = local.replace(hour=10, minute=0).floor("minute").datetime
    late_time = local.replace(hour=8, minute=30).floor("minute").datetime

    need_punish = True if local > punish_time else False

    punish_m_type = "man_sign_in"
    man_m_type = "parttime"

    absent_money = 300
    late_money = 50
    date_str = "%s年%s月%s日" % (local.year, local.month, local.day)

    absent_msg = "%s最终判定为旷工，现处以%s元的罚款，如你当日已经请假，请尽快向上级反映；奖惩明细可以到风先生软件内的数据页面查看" % (date_str, absent_money)
    late_msg = "%s最终判定为迟到，现处以%s元的罚款；奖惩明细可以到风先生软件内的数据页面查看" % (date_str, late_money)

    logging.info("sign_in man start...")

    log = []
    windchat = []
    punishment = []

    # ===================== processing =============================
    def process(tel):
        # 为什么在这里进行链接呢
        # 为了后面可以扩展成multiprocessing, 多线程中如果使用同一个数据库链接会出错
        man_conn = mongodb_client['profile']['man']
        sign_conn = mongodb_client['profile']['sign_in']
        cursor = node_conn.cursor()

        # 检查是否有这个人
        man = man_conn.find_one({"tel": tel})
        if not man:
            log.append([tel, "这个配送员没有注册"])
            return
        man = format_man(man, man_m_type)

        # 获取应该签到的点
        node = find_man_node(cursor, man['id'])
        if not node:
            log.append([tel, man['name'], "没有这个配送员的网点信息, 请管理人员在后台给他设置"])
            return
        node_name, lng, lat = node

        # 获取签到数据
        doc = sign_conn.find({
            "tel": tel,
            "create_time": {
                "$gte": start,
                "$lte": end,
            }
        }, sort=[['create_time', 1]])

        sign = man_find_first_valid_sign(doc, lng, lat)

        if not sign:
            log.append([tel, man['name'], "无有效的签到数据"])
            windchat.append(dict(man=man, title="惩罚提醒", content=absent_msg, summary=absent_msg,
                                 description="惩罚提醒"))
            if need_punish:
                punishment.append(
                    Rewards(man=man, m_type=punish_m_type, title="旷工惩罚", desc="无有效的签到数据", money=-absent_money,
                            create_time=local.datetime)
                )
            return

        t = arrow.get(sign['create_time'], "utc").to("local").datetime
        if t > late_time:
            log.append([tel, man['name'], "迟到", sign['loc']['addr'], sign['loc']['name'], t.strftime(TIME_PATTERN)])
            windchat.append(dict(man=man, title="惩罚提醒", content=late_msg, summary=late_msg,
                                 description="惩罚提醒"))
            if need_punish:
                punishment.append(
                    Rewards(man=man, m_type=punish_m_type, title="迟到惩罚", desc="迟到", money=-late_money,
                            create_time=local.datetime)
                )

            return

        log.append([tel, man['name'], "签到成功", sign['loc']['addr'], sign['loc']['name'], t.strftime(TIME_PATTERN)])

    # =======================================================================

    for tel in man_list:
        process(tel)

    # ====== 统一进行处理, 便于DEBUG ======
    # 风信
    from tools_lib.windchat import shortcuts, conf
    for wind in windchat:
        man = wind.pop('man')
        # 获取风信ID
        wc_id_list = shortcuts.account_query(
            account={"account_id": man['id'], "account_type": conf.ACCOUNT_TYPE_MAN})
        if not wc_id_list:
            log.append([man['tel'], man['name'], "无风信账户"])
            continue
        client_id = wc_id_list[0]

        shortcuts.channel_send_message(client_id, **wind)

    # 惩罚
    for _ in punishment:
        _.save()

    # 邮件和日志
    msg = [["电话", "姓名", "标记", "地址", "POI", "签到时间"]]

    for _ in log:
        logging.info(safe_join(_))
        msg.append(_)

    try:
        if DEBUG:
            send_mail(mail_list, "[测试]派件员签到报表", "这是测试服务器发出的测试数据\n数据日期:" + str(local), file_name="data.xls",
                      file_stream=xls_writer(msg))
        else:
            send_mail(mail_list, "派件员签到报表", "这是线上服务器发出的线上数据\n数据日期:" + str(local), file_name="data.xls",
                      file_stream=xls_writer(msg))
    except Exception as e:
        logging.exception(e.message)

    logging.info("sign_in man end...")
    return True


@once("driver_sign_in", days=0)
def driver(days=0):
    local = arrow.now().replace(days=days)
    if local.hour < 23:
        return False

    # 初始化时间
    node_conn = psycopg2.connect(cursor_factory=psycopg2.extras.DictCursor, database="tlbs", **CONFIG_POSTGRESQL)

    need_punish = True if local > punish_time else False
    punish_m_type = "driver_sign_in"
    man_m_type = "city_driver"

    absent_money = 300
    late_money = 30
    if need_punish:
        late_msg = "%s年%s月%s日你在{}{}点{}分迟到，现处以%s元的罚款；奖惩明细可以到风先生软件内的数据页面查看" % (
            local.year, local.month, local.day, late_money)

        absent_msg = "%s年%s月%s日你旷工，现处以%s元的罚款，如你当日已经请假，请尽快向上级反映；奖惩明细可以到风先生软件内的数据页面查看" % (
            local.year, local.month, local.day, absent_money)
    else:
        late_msg = "%s年%s月%s日你在{}{}点{}分迟到，予以警告处理；2016年6月1日起此行为会被处以%s元/次的罚款，请注意不要再犯。" % (
            local.year, local.month, local.day, late_money)
        absent_msg = "%s年%s月%s日你旷工，予以警告处理；2016年6月1日起此行为会被处以%s元/次的罚款，请注意不要再犯。" % (
            local.year, local.month, local.day, absent_money)

    log = []
    windchat = []
    punishment = []
    logging.info("sign_in driver start...")

    # ===================== processing =============================
    def process(tel):
        man_conn = mongodb_client['profile']['man']
        cursor = node_conn.cursor()

        # 检查是否有这个人
        man = man_conn.find_one({"tel": tel})
        if not man:
            logging.info("tel[%s], 这个司机没有注册", tel)
            return
        man = format_man(man, man_m_type)

        node_list = find_driver_node(cursor, man['id'])
        if not node_list:
            log.append([tel, man['name'], "这个司机没有线路网点信息, 请管理人员设置"])
            return

        # ============= 旷工 =============
        cursor.execute(
            """SELECT count(*)
            from trans.bs_trans_deliver_sign_record
            where deliver_id = %s and create_time >= %s and create_time <= %s
            """,
            (man['id'], local.floor("day").strftime(TIME_PATTERN), local.ceil("day").strftime(TIME_PATTERN))
        )

        doc = cursor.fetchone()
        if not doc or int(doc[0]) == 0:
            log.append([tel, man['name'], "旷工"])
            windchat.append(dict(man=man, title="惩罚提醒", content=absent_msg, summary=absent_msg, description="惩罚提醒"))
            punishment.append(
                Rewards(man=man, m_type=punish_m_type, title="旷工惩罚", desc="旷工", money=-absent_money,
                        create_time=local.datetime)
            )
            punishment.append(
                Rewards(man=man, m_type=punish_m_type, title="旷工惩罚", desc="因为旷工扣除今天的基础服务费", money=-DRIVER_BASE,
                        create_time=local.datetime)
            )

            return
        # ============================

        for node in node_list:

            node_name, lng, lat, hour, minute = node

            msg = late_msg.format(node_name, hour, minute)
            time = local.replace(hour=hour, minute=minute).floor('minute')
            e = time.datetime
            s = time.replace(minutes=-20).datetime

            sign = driver_find_first_valid_sign(cursor, man['id'], s.strftime(TIME_PATTERN), e.strftime(TIME_PATTERN),
                                                lng, lat)
            if not sign:
                log.append([tel, man['name'], "迟到", node_name, "%02d:%02d" % (hour, minute)])
                windchat.append(dict(man=man, title="惩罚提醒", content=msg, summary=msg, description="惩罚提醒"))
                desc = "在%s%s点%s分迟到" % (node_name, hour, minute)
                punishment.append(Rewards(man=man, m_type=punish_m_type, title="迟到惩罚", desc=desc, money=-late_money,
                                          create_time=local.datetime))

                continue

            # 已经转好时区
            t = sign['create_time']

            log.append([tel, man['name'], "签到成功", node_name, "%02d:%02d" % (hour, minute), t.strftime(TIME_PATTERN)])

    # =========================================

    # main process
    for tel in driver_list:
        process(tel)
    # ==========================================
    # 风信
    from tools_lib.windchat import shortcuts, conf
    for wind in windchat:
        man = wind.pop('man')
        # 获取风信ID
        wc_id_list = shortcuts.account_query(
            account={"account_id": man['id'], "account_type": conf.ACCOUNT_TYPE_MAN})
        if not wc_id_list:
            log.append([man['tel'], man['name'], "无风信账户"])
            continue
        client_id = wc_id_list[0]

        shortcuts.channel_send_message(client_id, **wind)

    # 惩罚
    for _ in punishment:
        _.save()

    # 日志和邮件
    msg = [["电话", "姓名", "标记", "站点", "需要到达时间", "签到时间"]]

    for _ in log:
        logging.info(safe_join(_))
        msg.append(_)

    try:
        if DEBUG:
            send_mail(mail_list, "[测试]司机签到报表", "这是测试服务器发出的测试数据\n数据日期:" + str(local), file_name="data.xls",
                      file_stream=xls_writer(msg))
        else:
            send_mail(mail_list, "司机签到报表", "这是线上服务器发出的线上数据\n数据日期:" + str(local), file_name="data.xls",
                      file_stream=xls_writer(msg))
    except Exception as e:
        logging.exception(e.message)

    logging.info("sign_in driver end...")

    return True


def windchat():
    from .utils import man_list
    from tools_lib.windchat import shortcuts, conf

    local = arrow.now()
    man_conn = mongodb_client['profile']['man']
    man_m_type = "parttime"

    id_list = []

    for tel in man_list:
        # 检查是否有这个人
        man = man_conn.find_one({"tel": tel})
        if not man:
            continue
        man = format_man(man, man_m_type)

        wc_id_list = shortcuts.account_query(
            account={"account_id": man['id'], "account_type": conf.ACCOUNT_TYPE_MAN})
        if not wc_id_list:
            continue
        id_list.append(wc_id_list[0])

    if local.hour == 8 and local.minute == 20:
        msg = "离签到截止时间还剩10分钟，请尽快到集结地签到；如已签到请忽略此条消息"
        shortcuts.channel_send_message(id_list, title="签到提醒", content=msg, summary=msg, description="签到提醒")
    elif local.hour == 8 and local.minute == 30:
        msg = "签到时间已到，如未签到将做迟到处理并罚款50元；如果10：00仍未签到，将升级为旷工并罚款300元，请尽快到集结地签到；如已签到请忽略此条消息"
        shortcuts.channel_send_message(id_list, title="签到提醒", content=msg, summary=msg, description="签到提醒")
    elif local.hour == 9 and local.minute == 50:
        msg = "如还未签到，10分钟后将视为旷工并罚款300元，请尽快到集合地签到；如已签到请忽略此消息"
        shortcuts.channel_send_message(id_list, title="签到提醒", content=msg, summary=msg, description="签到提醒")


if __name__ == "__main__":
    import sys
    import os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
    # print CONFIG_POSTGRESQL
    # print DEBUG
    # print mongo_client
    from settings import MONGODB_NAME
    from tools_lib.gmongoengine.connnection import connect

    connect(MONGODB_NAME, alias='aeolus_connection')
    logging.root.level = logging.INFO
    # 补数据用, 别乱跑
    days = -1
    # man(days)
    driver(days)
