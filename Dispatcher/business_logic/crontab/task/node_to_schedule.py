# coding:utf-8

from tools_lib.common_util.log import simple_conf_init

simple_conf_init()

import random
import logging
import requests
import json
import arrow
import time
import datetime
from schema import Schema, SchemaError, Optional
from .utils import once
from tools_lib.gtornado.escape import schema_unicode, schema_unicode_empty


@once('am', days=0)
def do_daily_routine_am(days=0):
    mission_ids = _get_tasks()
    for mid in mission_ids:
        _do_it_am(mid)


@once('pm', days=0)
def do_daily_routine_pm(days=0):
    mission_ids = _get_tasks()
    for mid in mission_ids:
        _do_it_pm(mid)


def _get_tasks():
    url = 'http://api.gomrwind.com:5000/WindMission/mission/management/list/page?pageno=1&pagesize=10'
    resp_obj = requests.get(url, headers={'Authorization': '1697f427f41f0a9f866ee28d51dc952d'})
    if 200 <= resp_obj.status_code < 300:
        # print(json.dumps(json.loads(resp_obj.content), ensure_ascii=False, indent=2))
        try:
            resp = Schema({
                "message": "成功",
                "code": "1",
                'content': [
                    {
                        # "act": 1,
                        # "arrivalAddress": "江陵路2013号星耀城1期101号(么么哒美食对面)",
                        # "arrivalLat": 30.213917,
                        # "arrivalLng": 120.21466,
                        "arrivalTime": schema_unicode,
                        # "createTime": "2016-11-24T07:30:01+0800",
                        # "endTime": "2016-11-24T18:06:00+0800",
                        # "executorUserId": "",
                        # "executorUserType": "",
                        "missionId": schema_unicode,
                        # "orderUserType": "",
                        "status": schema_unicode_empty,
                        # "tag": "",
                        # "tagList": [],
                        "title": schema_unicode_empty,  # "考勤签到"/"碰面任务",
                        "type": schema_unicode,  # "ATTENDANCE"
                        Optional(object): object
                    }
                ]
            }).validate(json.loads(resp_obj.content))
            tasks = resp['content']
            ids = []
            for t in tasks:
                if t['type'] == "ATTENDANCE" and t['status'] not in ['COMPLETE', 'CLOSE']:
                    ids.append(t['missionId'])
                else:
                    continue
            return ids
        except SchemaError as e:
            logging.error(e.message)
            return []


def _get_seperated_tasks():
    url = 'http://api.gomrwind.com:5000/WindMission/mission/management/list/page?pageno=1&pagesize=10'
    resp_obj = requests.get(url, headers={'Authorization': '53616e9cbe91b9ea648ced648923e146'})
    if 200 <= resp_obj.status_code < 300:
        # print(json.dumps(json.loads(resp_obj.content), ensure_ascii=False, indent=2))
        try:
            resp = Schema({
                "message": "成功",
                "code": "1",
                'content': [
                    {
                        # "act": 1,
                        # "arrivalAddress": "江陵路2013号星耀城1期101号(么么哒美食对面)",
                        # "arrivalLat": 30.213917,
                        # "arrivalLng": 120.21466,
                        "arrivalTime": schema_unicode,
                        # "createTime": "2016-11-24T07:30:01+0800",
                        # "endTime": "2016-11-24T18:06:00+0800",
                        # "executorUserId": "",
                        # "executorUserType": "",
                        "missionId": schema_unicode,
                        # "orderUserType": "",
                        "status": schema_unicode_empty,
                        # "tag": "",
                        # "tagList": [],
                        "title": schema_unicode_empty,  # "考勤签到"/"碰面任务",
                        "type": schema_unicode,  # "ATTENDANCE"
                        Optional(object): object
                    }
                ]
            }).validate(json.loads(resp_obj.content))
            tasks = resp['content']
            ids, meet_ups = [], []
            for t in tasks:
                if t['type'] == "ATTENDANCE" and t['status'] not in ['COMPLETE', 'CLOSE']:
                    if t['title'] == '考勤签到':
                        ids.append(t['missionId'])
                    elif t['title'] == '碰面任务':
                        meet_ups.append(t['missionId'])
                else:
                    continue
            return ids, meet_ups
        except SchemaError as e:
            logging.error(e.message)
            return [], []


def _do_it_am(mission_id):
    sign_in = arrow.now().replace(hour=9, minute=0)

    now = arrow.now()

    # 距离开始10min
    while (sign_in - now) > datetime.timedelta(minutes=10):
        logging.info('还没到该做这件事的时间[%s], 等待30s...' % sign_in)
        time.sleep(30)
        now = arrow.now()
    else:
        if (sign_in - now) < datetime.timedelta():
            logging.info('太晚了...')
        else:
            url = 'http://api.gomrwind.com:5000/WindMission/mission/attendance/operateSign'
            body = {
                "missionId": mission_id,
                "locationLat": "30.213917",
                "locationLng": "120.21466",
                "locationAddress": "江陵路2013号星耀城1期101号(么么哒美食对面)"
            }
            resp_obj = requests.post(url, json=body)
            # print(json.dumps(resp_obj.content, ensure_ascii=False, indent=2))


def _do_it_pm(mission_id):
    sign_off = arrow.now().replace(hour=21).replace(minutes=11)

    now = arrow.now()

    # 距离结束10min
    while (now - sign_off) < datetime.timedelta(minutes=10):
        logging.info('还没到该做这件事的时间[%s], 等待30s...' % sign_off)
        time.sleep(30)
        now = arrow.now()
    else:
        url = 'http://api.gomrwind.com:5000/WindMission/mission/attendance/operateSign'
        body = {
            "missionId": mission_id,
            "locationLat": "30.213917",
            "locationLng": "120.21466",
            "locationAddress": "江陵路2013号星耀城1期101号(么么哒美食对面)"
        }
        resp_obj = requests.post(url, json=body)
        print((json.dumps(resp_obj.content, ensure_ascii=False, indent=2)))


def do_cliche():
    pseudo = random.randint(1, 8)
    time.sleep(60 * pseudo)
    a, b = _get_seperated_tasks()
    for mission_id in a:
        url = 'http://api.gomrwind.com:5000/WindMission/mission/attendance/operateSign'
        body = {
            "missionId": mission_id,
            "locationLat": "30.213917",
            "locationLng": "120.21466",
            "locationAddress": "江陵路2013号星耀城1期101号(么么哒美食对面)"
        }
        resp_obj = requests.post(url, json=body)
        print((json.dumps(resp_obj.content, ensure_ascii=False, indent=2)))

    for mission_id in b:
        url = 'http://api.gomrwind.com:5000/WindMission/mission/attendance/operateSign'
        body = {
            "missionId": mission_id,
            "locationLat": 0,
            "locationLng": 0,
            "locationAddress": "",
            "effectorId": "11e62c84f2632d70bdaf22266a250d8f"
        }
        resp_obj = requests.post(url, json=body)
        print((json.dumps(resp_obj.content, ensure_ascii=False, indent=2)))


if __name__ == "__main__":
    c, d = _get_seperated_tasks()
    print((c, d))
