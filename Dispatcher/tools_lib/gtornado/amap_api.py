# coding:utf-8
from __future__ import unicode_literals
import json
import logging
import random

from tornado import gen, httpclient
from tornado.httpclient import HTTPRequest, HTTPError
from tornado.httputil import url_concat  # GET方法组装参数

amap_walking_url = "http://restapi.amap.com/v3/direction/walking"
amap_geocode_url = "http://restapi.amap.com/v3/geocode/geo"
"""
高德开发者Key：
风先生Android收派端 1685194faa1576e33f0322c74b44e6d7
风先生Web服务API c2da11a4537c64e2ef4233ba919cfcbd
风先生iOS发货端 26eaed54962dc5c1f3c88a6f881e81f3

孙超杰
测试01  442564273d59cbac39919ff2c6eb43df
测试02  8d08d7110c92605f950a2e169acd09ee
测试03  3aa614d8ac51f2e600836a7e6dc31e25
测试04  e54920ca5504f89dea777de4906a23e2
"""

key_list = [
    "538e250d2741dc084117c0dff1673272",  # mio
    "c2da11a4537c64e2ef4233ba919cfcbd"  # 风先生普通
]


@gen.coroutine
def amap_get_distance(from_lng, from_lat, to_lng, to_lat):
    """
    高德地图获取步行距离
    :param from_lng:
    :param from_lat:
    :param to_lng:
    :param to_lat:
    :return:
    """
    params = dict(
        origin=",".join((str(from_lng), str(from_lat))),
        destination=",".join((str(to_lng), str(to_lat))),
        key=random.choice(key_list)
    )
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(
            HTTPRequest(url=url_concat(amap_walking_url, params), method="GET", request_timeout=0.5))
        response = json.loads(response.body)
        distance = int(response['route']['paths'][0]['distance'])
    except HTTPError:
        logging.info("***___!!!__*** Amap Walking Distance Cal Timeout ***___!!!__***")
        raise gen.Return((0, "timeout"))
    except Exception:
        logging.info("***___!!!__*** Amap Walking Distance Cal Exception ***___!!!__***")
        raise gen.Return((0, "exception"))
    else:
        raise gen.Return((distance, "ok"))


@gen.coroutine
def amap_geocode(address):
    """
    高德地图，通过地址解析经纬度
    :param address:
    :return: return latitude, longitude
    """
    params = dict(
        address=address,
        output="json",
        key=random.choice(key_list)
    )
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(
            HTTPRequest(url=url_concat(amap_geocode_url, params), method="GET", request_timeout=0.5))
        response = json.loads(response.body)
        lat, lng = response['geocodes'][0]['location'].split(',')[::-1]
    except HTTPError:
        logging.error("***___!!!__*** Amap Geocode Timeout ***___!!!__***")
        raise gen.Return([None, None])
    except Exception:
        logging.error("***___!!!__*** Amap Geocode Failed ***___!!!__***")
        raise gen.Return([None, None])
    else:
        raise gen.Return([lng, lat])
