#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals

import json

from pymongo import MongoClient
from tools_lib.common_util.sstring import safe_unicode

PROD = '123.56.117.75'
DEV = '123.57.45.209'

# 存储 站点-时刻-配送员 的对应信息
# {time_table: { $elemMatch: { mans: {$elemMatch: {tel: { $regex: '91', $options: 'i' } } } }}}
mc = MongoClient(host=DEV, port=27017)['aeolus']['node']

"""
time,name,username,userid,clientid
西湖站,余杭塘路/学院路路口（诗曼油压养生）,,"30.3010580000,120.1346380000",
09:10,刘从志,18218711837,56c811a27f452563e439bcb6,bd74cd1296da48ed8e1a5248c62d6166
13:30,刘从志,18218711837,56c811a27f452563e439bcb6,bd74cd1296da48ed8e1a5248c62d6166
14:30,刘从志,18218711837,56c811a27f452563e439bcb6,bd74cd1296da48ed8e1a5248c62d6166
18:40,刘从志,18218711837,56c811a27f452563e439bcb6,bd74cd1296da48ed8e1a5248c62d6166
10:10,张运兵,18756236888,56c7c2527f452563e439bcb3,8a2170abbcbe4aa4bfa54f6559cdcb97
15:20,张运兵,18756236888,56c7c2527f452563e439bcb3,8a2170abbcbe4aa4bfa54f6559cdcb97
19:40,张运兵,18756236888,56c7c2527f452563e439bcb3,8a2170abbcbe4aa4bfa54f6559cdcb97
11:20,朱立忠,13735469767,56f4e40ceed0932e4a19c027,9e4ea7d08b3a4c779d7818d97355f586
16:20,朱立忠,13735469767,56f4e40ceed0932e4a19c027,9e4ea7d08b3a4c779d7818d97355f586
12:20,彭永红,18758888361,5705d790eed093542eb1ea11,da443c6a4e5a47ac9f8155ce242bcb5f
13:30,彭永红,18758888361,5705d790eed093542eb1ea11,da443c6a4e5a47ac9f8155ce242bcb5f
17:30,彭永红,18758888361,5705d790eed093542eb1ea11,da443c6a4e5a47ac9f8155ce242bcb5f
笕桥站,杭州江干区双凉环路,,"30.3173080000,120.2201820000",
09:10,郑飞,13082823376,56c66f1c7f452563e439bca4,57c9189b55d44c91a8c09d7b57b57513
13:30,郑飞,13082823376,56c66f1c7f452563e439bca4,57c9189b55d44c91a8c09d7b57b57514
14:30,郑飞,13082823376,56c66f1c7f452563e439bca4,57c9189b55d44c91a8c09d7b57b57515
18:40,郑飞,13082823376,56c66f1c7f452563e439bca4,57c9189b55d44c91a8c09d7b57b57516
10:10,姚磊,13575498576,56e17b28eed093310861162b,dae0929ec4b6417b9b1de8a27954f942
15:20,姚磊,13575498576,56e17b28eed093310861162b,dae0929ec4b6417b9b1de8a27954f942
19:40,姚磊,13575498576,56e17b28eed093310861162b,dae0929ec4b6417b9b1de8a27954f942
11:20,章成龙,18668760225,56fb30b5eed093338d22a919,1c85f1b222084688bf60bbc0aadb9a5a
"""
if __name__ == '__main__':
    nodes = []
    count = 0

    with open('从csv拿node.csv', 'r') as f:
        for line in f:
            count += 1
            values = line.strip().replace(b'\"', b'').split(b',')
            parsed = []
            for v in values:
                if v:
                    parsed.append(safe_unicode(v))

            print('%s: %s' % (len(parsed), parsed))
            # 站点基本信息行: 萧山站,杭州萧山区建设一路金一路路口,,"30.2012140000,120.2662010000"
            if len(parsed) == 4:
                name = parsed[0]
                address = parsed[1]
                lat = round(float(parsed[2]), 10)
                lng = round(float(parsed[3]), 10)
                node_basic = dict(name=name, loc={'lat': lat, 'lng': lng, 'address': address})
                nodes.append(node_basic)
                # 不是第一个站点基本信息行, 将上一个站点信息记入mongodb
                if len(nodes) > 1:
                    print(json.dumps(nodes[-2], ensure_ascii=False, indent=2))
                    # sort node.time_table
                    node = nodes[-2]
                    tt = sorted(node['time_table'],
                                lambda x, y: cmp(x['t'], y['t']) if x['t'] != y['t'] else cmp(x['man']['id'], y['man']['id']))
                    node['time_table'] = tt
                    nodes[-2] = node
                    # 记入db
                    mc.insert_one(nodes[-2])
            # 时刻行: 11:20,郑飞,13082823376,56c66f1c7f452563e439bca4,57c9189b55d44c91a8c09d7b57b57515
            elif len(parsed) == 5 and count != 1:
                t = parsed[0]
                name = parsed[1]
                tel = parsed[2]
                user_id = parsed[3]
                client_id = parsed[4]
                man = dict(name=name, tel=tel, id=user_id, client_id=client_id, m_type='driver')
                time_row = dict(t=t, man=man)
                if 'time_table' not in nodes[-1]:
                    nodes[-1]['time_table'] = [time_row]
                else:
                    nodes[-1]['time_table'].append(time_row)
        # sort node.time_table
        node = nodes[-1]
        tt = sorted(node['time_table'],
                    lambda x, y: cmp(x['t'], y['t']) if x['t'] != y['t'] else cmp(x['man']['id'], y['man']['id']))
        node['time_table'] = tt
        nodes[-1] = node
        mc.insert_one(nodes[-1])


