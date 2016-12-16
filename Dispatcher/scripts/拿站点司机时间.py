#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals
import psycopg2
import arrow
import json

if __name__ == '__main__':
    conn = None
    try:
        conn = psycopg2.connect(host='182.92.115.196', port='5432', database='tlbs', user='postgres', password='feng123')
    except Exception as e:
        print(e.message)
        exit(-1)

    cursor = conn.cursor()
    cursor.execute("""select
    c.node_id,c.deliver_id,c.reg_cron,d.node_name,ST_AsGeoJSON(d.loc) as loc,d.node_address
    from
        (select a.node_id,a.deliver_id,b.reg_cron from trans.bs_trans_bind_node_info as a
        left join trans.bs_trans_reg_time as b
        on a.cron_id=b.id
        where a.status = 1) as c
    left join trans.bs_trans_node_info as d
    on c.node_id=d.node_id;""")
    # node_id                              deliver_id                   reg_cron        node_name loc                                                        node_address
    # 11e603b4722edfd025342a53cbd7fae9    56fb30b5eed093338d22a919    0 30 9 * * ?    星耀城    {"type":"Point","coordinates":[120.221344,30.219355]}    杭州市滨江区星耀城
    orbit = []
    schedule_today = {}

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
        if man_id not in schedule_today:
            schedule_today[man_id] = dict(run=[footprint])
        else:
            schedule_today[man_id]['run'].append(footprint)

    conn.close()

    # 算orbit, 给t排序
    for key in nodes:
        node = nodes[key]
        t_list = node['t']
        node['t'] = sorted(t_list)
        orbit.append(node)

    # 给schedule_today[man_id][run]排序
    for key in schedule_today:
        schedule = schedule_today[key]
        schedule['run'] = sorted(schedule['run'], cmp=lambda x, y: cmp(x['t'], y['t']))

    print(json.dumps(orbit, ensure_ascii=False, indent=2))
    print(json.dumps(schedule_today, ensure_ascii=False, indent=2))
