#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals

import json
from pymongo import MongoClient
from schema import Schema, Optional
from tools_lib.gtornado.escape import schema_unicode, schema_float, schema_objectid

PROD = '123.56.117.75'
DEV = '123.57.45.209'
host = PROD
# 存储 站点-时刻-配送员 的对应信息
mcs = MongoClient(host=host, port=27017)['aeolus']['schedule']
# 存储 站点-时刻-配送员 的对应信息
# {time_table: { $elemMatch: { mans: {$elemMatch: {tel: { $regex: '91', $options: 'i' } } } }}}
mcn = MongoClient(host=host, port=27017)['aeolus']['node']


def node_to_schedule(_mcn, _mcs):
    node_schema = Schema({
        'name': schema_unicode,
        'loc': {
            'lat': schema_float,
            'lng': schema_float,
            'address': schema_unicode,
        },
        'time_table': [
            {
                't': schema_unicode,
                'man': {
                    'id': schema_objectid,
                    'name': schema_unicode,
                    'tel': schema_unicode,
                    Optional('m_type', default='driver'): schema_unicode,
                    'client_id': schema_unicode
                }
            }
        ]
    })
    schedule_schema = Schema([
        {
            'man': {
                'id': schema_objectid,
                'name': schema_unicode,
                'tel': schema_unicode,
                Optional('m_type', default='driver'): schema_unicode,
                'client_id': schema_unicode
            },
            'run': [
                {
                    't': schema_unicode,
                    'name': schema_unicode,
                    'loc': {
                        'lat': schema_float,
                        'lng': schema_float,
                        'address': schema_unicode,
                    }
                }
            ]
        }
    ])

    schedules = {}  # {man.id: his_schedule}
    nodes = _mcn.find({})
    for node in nodes:
        name = node['name']
        loc = node['loc']
        time_table = node['time_table']
        for time_man in time_table:
            t = time_man['t']
            man = time_man['man']  # id, name, tel, m_type, client_id
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
    print('\n校验node到schedule:')
    for man_id in schedules:
        schedule = schedules[man_id]
        s_cursor = _mcs.find({'man.id': man_id}, {'_id': 0})
        for doc in s_cursor:
            print('%s: %s' % (schedule['man']['name'], schedule == doc))
    return schedules


def schedule_to_node(_mcs, _mcn, is_check=True):
    nodes = {}  # {node.name: node}
    schedules = _mcs.find({})
    for schedule in schedules:
        man = schedule['man']  # id, name, tel, m_type, client_id
        run = schedule['run']  # [{t=t, name=name, loc={lat,lng,address}},...]
        for time_node in run:
            t = time_node['t']
            if time_node['name'] not in nodes:
                nodes[time_node['name']] = {
                    'name': time_node['name'],
                    'loc': time_node['loc'],
                    'time_table': [
                        {
                            't': t,
                            'man': man
                        }
                    ]
                }
            else:
                nodes[time_node['name']]['time_table'].append(
                    {
                        't': t,
                        'man': man
                    }
                )
    # sort node.time_table
    for name in nodes:
        node = nodes[name]
        tt = sorted(node['time_table'],
                    lambda x, y: cmp(x['t'], y['t']) if x['t'] != y['t'] else cmp(x['man']['id'], y['man']['id']))
        node['time_table'] = tt
        nodes[name] = node
    # compare nodes with Node.objects
    if is_check:
        print('\n校验schedule到node:')
        for name in nodes:
            node = nodes[name]
            n_cursor = _mcn.find({'name': name}, {'_id': 0})
            for doc in n_cursor:
                doc.pop('point')
                print('%s: %s' % (name, node == doc))
                if node != doc:
                    print('why not?')
                    for k in node:
                        print('%s: %s' % (k, node[k] == doc[k]))
    else:
        print('\n根据schedule生成node:')
        for name in nodes:
            node = nodes[name]
            _mcn.insert_one(node)
            print(name)
    return nodes


if __name__ == '__main__':
    node_to_schedule(mcn, mcs)
    schedule_to_node(mcs, mcn)
