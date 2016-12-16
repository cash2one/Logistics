#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals

from pymongo import MongoClient
from tools_lib.common_util.sstring import safe_unicode

# from tools_lib.account import ROLE_TAG_MAN, ROLE_TAG_DRIVER
# 角色标签
ROLE_TAG_MAN = "man"
ROLE_TAG_DRIVER = "driver"

PROD = '123.56.117.75'
DEV = '123.57.45.209'

# 存储 站点-时刻-配送员 的对应信息
mc = MongoClient(host=DEV, port=27017)['aeolus']['schedule']
"""
王迎远,18895643469,56fb5435eed0931146f39762,2e0951189fa540acb04e38c12e21c90d,司机
12:20,笕桥站,杭州江干区双凉环路,"30.3173080000,120.2201820000",
13:30,笕桥站,杭州江干区双凉环路,"30.3173080000,120.2201820000",
17:30,笕桥站,杭州江干区双凉环路,"30.3173080000,120.2201820000",
10:10,滨江站,杭州滨江区时代大道/南环路（路口）,"30.1830070000,120.1949550000",
15:20,滨江站,杭州滨江区时代大道/南环路（路口）,"30.1830070000,120.1949550000",
19:40,滨江站,杭州滨江区时代大道/南环路（路口）,"30.1830070000,120.1949550000",
11:20,上城站,杭州上城区老浙大横路27号,"30.2600490000,120.1910920000",
14:20,上城站,杭州上城区老浙大横路27号,"30.2600490000,120.1910920000",
16:30,上城站,杭州上城区老浙大横路27号,"30.2600490000,120.1910920000",
18:50,上城站,杭州上城区老浙大横路27号,"30.2600490000,120.1910920000",
陈海舟,15962871675,5719b1f8eed09376976b367c,1214ad15c4b94d89a32227c5dfbc04fc,收派员
08:30,西湖站,余杭塘路/学院路路口（诗曼油压养生）,"30.3010580000,120.1346380000",
"""


def dump_to_schedule(from_file, _mc):
    schedules = []
    count = 0
    with open(from_file, 'r') as f:
        for line in f:
            count += 1
            values = line.strip().replace(b'\"', b'').split(b',')
            parsed = []
            for v in values:
                if v:
                    parsed.append(safe_unicode(v))

            print('%s: %s: %s' % (count, len(parsed), ', '.join(parsed)))
            # 人员基本信息行: 刘从志,18218711837,56c811a27f452563e439bcb6,bd74cd1296da48ed8e1a5248c62d6166,司机
            if len(parsed) == 5 and count != 1 and parsed[4] in ('司机', '收派员'):
                name = parsed[0]
                tel = parsed[1]
                man_id = parsed[2]
                client_id = parsed[3]
                m_type = ROLE_TAG_MAN if parsed[4] == '收派员' else ROLE_TAG_DRIVER
                s_basic = dict(man={'id': man_id, 'name': name, 'tel': tel, 'm_type': m_type, 'client_id': client_id})
                schedules.append(s_basic)
                # 不是第一个站点基本信息行, 将上一个站点信息记入mongodb
                if len(schedules) > 1:
                    # sort schedule.run
                    schedule = schedules[-2]
                    run = sorted(schedule['run'], lambda x, y: cmp(x['t'], y['t']) if x['t'] != y['t'] else cmp(x['name'], y['name']))
                    schedule['run'] = run
                    schedules[-2] = schedule
                    # 记入db
                    _mc.insert_one(schedules[-2])
            # 时刻行: 09:10,西湖站,余杭塘路/学院路路口（诗曼油压养生）,"30.3010580000,120.1346380000"
            elif len(parsed) == 5 and count != 1:
                t = parsed[0]
                name = parsed[1]
                address = parsed[2]
                lat = round(float(parsed[3]), 10)
                lng = round(float(parsed[4]), 10)
                loc = dict(lat=lat, lng=lng, address=address)
                run_row = {
                    't': t,
                    'name': name,
                    'loc': loc,
                }
                if 'run' not in schedules[-1]:
                    schedules[-1]['run'] = [run_row]
                else:
                    schedules[-1]['run'].append(run_row)
        # sort schedule.run
        schedule = schedules[-1]
        run = sorted(schedule['run'], lambda x, y: cmp(x['t'], y['t']) if x['t'] != y['t'] else cmp(x['name'], y['name']))
        schedule['run'] = run
        schedules[-1] = schedule
        _mc.insert_one(schedules[-1])

if __name__ == '__main__':
    dump_to_schedule('从csv拿schedule2.csv', mc)
