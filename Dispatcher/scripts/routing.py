#!/usr/bin/env python
# coding:utf-8


import json

import arrow
import psycopg2
from haversine import haversine

# == 有用的函数 ==
# def haversine(lat1, lng1, lat2, lng2):
#     """
#     Calculate the great circle distance between two points
#     on the earth (specified in decimal degrees)
#     """
#     # convert decimal degrees to radians
#     lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
#
#     # haversine formula
#     dlon = lng2 - lng1
#     dlat = lat2 - lat1
#     a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
#     c = 2 * asin(sqrt(a))
#     r = 6371  # Radius of earth in kilometers. Use 3956 for miles
#     return c * r

_t0 = arrow.now()

# == 输入: 寄方,收方地址, 下单时间 ==
node = {
    "node_n": {
        "tel": "15868153486",
        "addr": "闻堰钱江渔村,223包厢",
        "fence": {
            "id": "56934bfd7df3484b702e2635",
            "name": "D2滨江浦沿"
        },
        "lat": 30.16571,  # 30.1364333583,
        "lng": 120.20178,  # 120.1773804353,
        "name": "来见平"
    },
    "node_0": {
        "tel": "18069812333",
        "name": "滨晨花艺",
        "fence": {
            "id": "568cf0bbf10f5b630d67f940",
            "name": "D1滨江"
        },
        "lat": 30.178808,
        "lng": 120.199628,
        "addr": "杭州市滨江区长江中路妇保医院对面"
    }
}

t0 = arrow.now().replace(minutes=+90).to("local").format('HH:mm')


# == 以下从于昕那里取: 放redis,ttl=24h ==
def get_orbit_and_schedule():
    conn = None
    try:
        conn = psycopg2.connect(host='182.92.115.196', port='5432', database='tlbs', user='postgres',
                                password='feng123')
    except Exception as e:
        print((e.message))
        exit(-1)

    cursor = conn.cursor()
    cursor.execute("""select
    c.node_id,c.deliver_id,c.reg_cron,d.node_name,ST_AsGeoJSON(d.loc) as loc,d.node_address
    from
        (select a.node_id,a.deliver_id,b.reg_cron from trans.bs_trans_bind_node_info as a
        left join trans.bs_trans_reg_time as b
        on a.cron_id=b.id
        where a.status = 1 and a.deliver_id is not NULL) as c
    left join trans.bs_trans_node_info as d
    on c.node_id=d.node_id;""")
    # node_id                              deliver_id                   reg_cron        node_name loc                                                        node_address
    # 11e603b4722edfd025342a53cbd7fae9    56fb30b5eed093338d22a919    0 30 9 * * ?    星耀城    {"type":"Point","coordinates":[120.221344,30.219355]}    杭州市滨江区星耀城
    _orbit = []
    _schedule_today = {}

    nodes = {}
    for record in cursor:
        ts = record[2].split(' ')
        hour = int(ts[2])
        mi = int(ts[1])
        t = arrow.now().replace(hour=hour if hour != 24 else 0, minute=int(mi))

        unicode_record = []
        for col in record:
            if isinstance(col, str):
                unicode_record.append(col.decode('utf-8'))
            else:
                unicode_record.append(col)

        man_id = unicode_record[1]
        node_id = unicode_record[0]
        node_name = unicode_record[3]
        node_address = unicode_record[5]
        t = t.format(fmt='HH:mm')
        coordinates = json.loads(unicode_record[4])['coordinates']
        coordinates = (coordinates[1], coordinates[0])  # (30.0, 120.0)把纬度放在前面

        # 捞nodes来算orbit: t没排序
        if node_id not in nodes:
            nodes[node_id] = dict(coordinates=coordinates, name=node_name, id=node_id, t=[t])
        else:
            nodes[node_id]['t'].append(t)

        # 算schedule_today: run没排序
        footprint = dict(coordinates=coordinates, name=node_name, id=node_id, t=t)
        if man_id not in _schedule_today:
            _schedule_today[man_id] = dict(run=[footprint])
        else:
            _schedule_today[man_id]['run'].append(footprint)

    conn.close()

    # 算orbit, 给t排序
    for key in nodes:
        node = nodes[key]
        t_list = node['t']
        node['t'] = sorted(t_list)
        _orbit.append(node)

    # 给schedule_today[man_id][run]排序
    for key in _schedule_today:
        schedule = _schedule_today[key]
        schedule['run'] = sorted(schedule['run'], cmp=lambda x, y: cmp(x['t'], y['t']))

    # print(json.dumps(_orbit, ensure_ascii=False, indent=2))
    # print(json.dumps(_schedule_today, ensure_ascii=False, indent=2))
    return _orbit, _schedule_today


orbit, schedule_today = get_orbit_and_schedule()


# == 解空间: 放redis,ttl=24h ==
def pre_calculated(_schedule_today):
    # Tn: t_pn+T派件; t_p0 > t0+T收件
    _answers = {}
    for driver in _schedule_today:
        run = _schedule_today[driver]['run']
        M = len(run)
        for i in range(M):
            for j in range(i, M):
                px = run[i]
                py = run[j]
                # (u'p1 p2')
                key = '%s %s' % (px['id'], py['id'])
                if key not in _answers:
                    _answers[key] = []
                _answers[key].append({'driver': driver, 'x': px, 'y': py})
    for a_key in _answers:
        # print(a_key, len(_answers[a_key]))
        pass
    # print(json.dumps(answers[a_key], ensure_ascii=False, indent=2, default=_dump))
    return _answers


answers = pre_calculated(schedule_today)


# == 优先计算服务时间 ==
def out_of_service_time(place_order_time, _orbit):
    service_s, service_e = '09:00', '17:00'
    for p in _orbit:
        start = min(p['t'])
        if start < service_s:
            service_s = start
        end = max(p['t'])
        if end > service_e:
            service_e = end
    if place_order_time < service_s or place_order_time > service_e:
        print(('已经超过我们的服务时间啦, 请在(%s,%s)内下单哦' % (service_s, service_e)))
    else:
        print(('好棒! 没超过我们的服务时间, 下单时间[%s]在(%s,%s)内哦' % (place_order_time, service_s, service_e)))


out_of_service_time(t0, orbit)


# == 输出1: 推荐始发站点, 推荐目的站点 ==
def find_nearby(_node, _orbit):
    limit_km_sj, limit_km_pj = 3, 5
    limit_count = 5
    _s0, _sn = [], []
    n0 = (_node['node_0']['lat'], _node['node_0']['lng'])
    nn = (_node['node_n']['lat'], _node['node_n']['lng'])
    for p in _orbit:
        # 算始发站点
        dist_0 = haversine(p['coordinates'], n0)
        if dist_0 < limit_km_sj:
            if len(_s0) < limit_count:
                _s0.append(dict(point=p, dist=dist_0, n0=n0))
            else:
                _s0 = sorted(_s0, cmp=lambda x, y: cmp(x['dist'], y['dist']))
                max_dist = _s0[-1]['dist']
                if dist_0 < max_dist:
                    _s0[-1] = dict(point=p, dist=dist_0, n0=n0)
        # 算目的站点
        dist_n = haversine(p['coordinates'], nn)
        if dist_n < limit_km_pj:
            if len(_sn) < limit_count:
                _sn.append(dict(point=p, dist=dist_n, nn=nn))
            else:
                _sn = sorted(_sn, cmp=lambda x, y: cmp(x['dist'], y['dist']))
                max_dist = _sn[-1]['dist']
                if dist_n < max_dist:
                    _sn[-1] = dict(point=p, dist=dist_n, nn=nn)
    print('始发站点:')
    print((json.dumps(_node['node_0'], ensure_ascii=False, indent=2)))
    print((json.dumps([dict(dist=_s['dist'], name=_s['point']['name']) for _s in _s0], ensure_ascii=False, indent=2)))
    print('目的站点:')
    print((json.dumps(_node['node_n'], ensure_ascii=False, indent=2)))
    print((json.dumps([dict(dist=_s['dist'], name=_s['point']['name']) for _s in _sn], ensure_ascii=False, indent=2)))

    if _s0 and _sn:
        print('找到可用站点, 需要进一步匹配时间和路线信息')
    if not _s0:
        print('找不到可用始发站点: 寄件地址太远了, 没法收件哦')
    if not _sn:
        print('找不到可用目的站点: 收件地址太远了, 没法派件哦')
    return _s0, _sn


s0, sn = find_nearby(node, orbit)


# == 输出2: 根据解空间推荐线路 ==
def make_guesses(_s0, _sn, _answers):
    recommend = {}
    _cnt = 0
    for i in _s0:
        for j in _sn:
            _cnt += 1
            p0_id, p1_id = i['point']['id'], j['point']['id']
            p = '%s %s' % (p0_id, p1_id)
            if p in _answers:
                print(('[✪✪✪][解%s] 找到一条路线能从[%s]到[%s], 进一步匹配时间信息.' % (_cnt, i['point']['name'], j['point']['name'])))
                ans_list = _answers[p]
                for ans in ans_list:
                    # 如果s0和sn中存在同一个站点, 优先推荐(不需要上车,直接派件)
                    if p0_id == p1_id:
                        recommend[p] = [
                            dict(confidence=1, driver='', x=i['point'], y=j['point'])]
                    # 需要赶车
                    elif ans['x']['t'] > t0:  # todo: 改成t0+t收件预计
                        if p not in recommend:
                            recommend[p] = []
                        # ans['confidence'] = 0.9  # todo: 改成根据合理的min(tx),min(ty)来给推荐指数
                        recommend[p].append(ans)
            else:
                print(('[   ][解%s] 没有一条路线能从[%s]到[%s].' % (_cnt, i['point']['name'], j['point']['name'])))

    if not recommend:
        print('找不到任何时段的可行路线: [预计明日送达]')
    else:
        print(('找到推荐(始发 终点 可选班次)个数为: %s, [预计今日送达]' % len(recommend)))

    for px_py in recommend:
        print((px_py, len(recommend[px_py])))
        print((json.dumps(recommend[px_py], ensure_ascii=False, indent=2)))
    return recommend


make_guesses(s0, sn, answers)
_t1 = arrow.now()

print(('搜寻解空间耗时: %s ' % (_t1 - _t0)))
