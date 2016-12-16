# coding:utf-8

import logging
from pymongo import MongoClient

from tools_lib.host_info import IP_MONGODB


def node_to_schedule(is_check=False):
    # 存储 站点-时刻-配送员 的对应信息
    _mcs = MongoClient(host=IP_MONGODB, port=27017)['aeolus']['schedule']
    # 存储 站点-时刻-配送员 的对应信息
    # {time_table: { $elemMatch: { mans: {$elemMatch: {tel: { $regex: '91', $options: 'i' } } } }}}
    _mcn = MongoClient(host=IP_MONGODB, port=27017)['aeolus']['node']

    schedules = {}  # {man.id: his_schedule}
    nodes = _mcn.find({})
    for node in nodes:
        name = node['name']
        loc = node['loc']
        time_table = node['time_table']
        for time_man in time_table:
            t = time_man['t']
            man = time_man.get('man')  # id, name, tel, m_type, client_id
            if not man:
                continue
            if man['id'] not in schedules:
                schedules[man['id']] = {
                    'man': man,
                    'run': [
                        {
                            't': t,
                            'name': name,
                            'loc': loc
                        }
                    ]
                }
            else:
                schedules[man['id']]['run'].append(
                    {
                        't': t,
                        'name': name,
                        'loc': loc
                    }
                )
    # sort schedule.run
    for man_id in schedules:
        schedule = schedules[man_id]
        run = sorted(schedule['run'], lambda x, y: cmp(x['t'], y['t']) if x['t'] != y['t'] else cmp(x['name'], y['name']))
        schedule['run'] = run
        schedules[man_id] = schedule
    # compare schedules with Schedule.objects
    if is_check:
        print('Compare node with schedule...')
        for man_id in schedules:
            schedule = schedules[man_id]
            s_cursor = _mcs.find({'man.id': man_id}, {'_id': 0})
            for doc in s_cursor:
                print('%s: %s' % (schedule['man']['name'], schedule == doc))
        print('Done.')
    else:
        print('Removing and recreating node to schedule...')
        _mcs.remove()
        _mcs.insert_many(schedules.values())
        print('Done.')


if __name__ == '__main__':
    PROD = '123.56.117.75'
    IP_MONGODB = PROD
    node_to_schedule(is_check=True)
