#!/usr/bin/env python
# coding: utf-8
# @Date    : 2015-09-07 15:19:48
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo
from __future__ import unicode_literals

import json
from random import randint

import async_requests
from tools_lib.common_util.sstring import safe_utf8
from tornado.web import gen

AK_BUFFER = [
    "sUiLz1vjhG212GBTnd5lZ8qw",
    "fudo2FQT2a57BlYmG8TNtWR5",
    "MlCrreOLOENQ8g4diEcVYpnh",
    "BCxvz1Cj51ilaf76ULAF5Iva",
    "MIp3BbV0YmtGX2VDqYVu12II",
    "SyXl5mIxG1ZOrCaNDTdCDIfn",
    "GpPGxVwFP1eEH0UOQpk9Xgsu",
    "xkZDTrLXGioD2ajPrKTBdHon",
    "TiNWpHzFPO25W7a94dEwS0yX",
    "6r6w6wFKiao9626G09UNKS8O"
]


def _get_ak():
    return AK_BUFFER[randint(0, len(AK_BUFFER) - 1)]


@gen.coroutine
def async_get_distance(from_lat, from_lng, to_lat, to_lng, region, origin_region, dest_region, mode='walking',
                       waypoints=None):
    """
    调用百度API获取不同模式下的距离
    百度API文档地址: http://developer.baidu.com/map/index.php?title=webapi/direction-api
    :param from_lat:
    :param from_lng:
    :param to_lat:
    :param to_lng:
    :param region:
    :param origin_region:
    :param dest_region:
    :param mode: 支持 walking(步行) / driving(驾车) / transit(公交)
    :param waypoints: 选填 途经点集合，包括一个或多个用竖线字符"|"分隔的地址名称或经纬度。支持驾车、公交方案，最多支持5个途经点。
    :return:
    """

    url = "http://api.map.baidu.com/direction/v1"
    params = {
        "mode": mode,
        "origin": "%f,%f" % (from_lat, from_lng),
        "destination": "%f,%f" % (to_lat, to_lng),
        "region": region,
        "origin_region": origin_region,
        "destination_region": dest_region,
        "output": "json",
        "ak": _get_ak()
    }
    if waypoints:
        params["waypoints"] = waypoints

    response = yield async_requests.get(url, params=params)
    distance = 0
    if response.code == 200:
        response = json.loads(response.body)
        if response['status'] == 0:
            distance = response['result']['routes'][0]['distance']

    # # 如果获取百度不成功的话
    # if distance == 0:
    #     distance = 1.5 * Mercator.distance(from_lng, from_lat, to_lng, to_lat)
    raise gen.Return(distance)


@gen.coroutine
def async_get_coordinates(city, district, address):
    """
    通过百度地图的API接口，将某个地址转换成经纬度坐标
    详情见：http://developer.baidu.com/map/webservice-placeapi.htm
    中的“5.2 Place检索示例”小节
    """
    if not city:
        city = '杭州市' if isinstance(address, unicode) else safe_utf8('杭州市')
    address = "%s %s %s" % (city, district, address)
    url = r"http://api.map.baidu.com/geocoder/v2/"
    params = {
        "ak": _get_ak(),
        "output": "json",
        "address": safe_utf8(address),
    }
    response = yield async_requests.get(url, params=params)
    lat = 0.0
    lng = 0.0
    if response.code == 200:
        data = json.loads(response.body)
        if data['status'] == 0:
            result = data['result']
            location = result.get("location")
            if result['confidence'] >= 20:
                lat = location.get("lat")
                lng = location.get("lng")
    # "lat" : 30.2592444615,
    # "lng" : 120.2193754157,

    raise gen.Return((lng, lat))


@gen.coroutine
def async_get_reverse_location(lng, lat):
    """
    文档:http://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-geocoding
    逆地理编码服务
    :param lng: 经度
    :param lat: 纬度
    :return:
    {
        "adcode": "110105",
        "city": "北京市",
        "country": "中国",
        "direction": "北",
        "distance": "68",
        "district": "朝阳区",
        "province": "北京市",
        "street": "花家地街",
        "street_number": "19号",
        "country_code": 0,
        "address": "北京市朝阳区花家地街19号四强写字楼北79米",
        "lng": 116.48088102568,
        "lat": 39.989410050151
    }
    """
    url = r"http://api.map.baidu.com/geocoder/v2/"
    params = {
        "ak": _get_ak(),
        "output": "json",
        "location": "{lat},{lng}".format(lat=lat, lng=lng),
    }
    response = yield async_requests.get(url, params=params)
    if response.code == 200:
        response = json.loads(response.body)
        address_component = response['result']['addressComponent']
        address_component['address'] = response['result']['formatted_address'] + \
                                       response['result']['sematic_description']
        address_component['lng'], address_component['lat'] = response['result']['location']['lng'], \
                                                             response['result']['location']['lat']
    else:
        address_component = {}
    raise gen.Return(address_component)


# 坐标转换
@gen.coroutine
def async_geoconv(lng, lat, fro=3):
    """
    将其他坐标系转换成百度坐标
    :param lng: 经度
    :param lat: 纬度
    :param from:
        1：GPS设备获取的角度坐标，wgs84坐标;

        2：GPS获取的米制坐标、sogou地图所用坐标;

        3：google地图、soso地图、aliyun地图、mapabc地图和amap地图所用坐标，国测局坐标;

        4：3中列表地图坐标对应的米制坐标;

        5：百度地图采用的经纬度坐标;

        6：百度地图采用的米制坐标;

        7：mapbar地图坐标;

        8：51地图坐标
    :return:
    """
    url = "http://api.map.baidu.com/geoconv/v1/?"
    params = {
        "from": fro,
        "to": 5,
        "coords": ",".join([str(lng), str(lat)]),
        "ak": _get_ak()
    }
    response = yield async_requests.get(url, params=params)
    lng, lat = 0.0, 0.0
    if response.code == 200:
        data = json.loads(response.body)
        if data['status'] == 0:
            loc = data['result'][0]
            lng = loc['x']
            lat = loc['y']

    raise gen.Return((lng, lat))


if __name__ == '__main__':
    from tornado.ioloop import IOLoop
    from functools import partial

    f = partial(async_get_coordinates, '', '', '飞虹路佳丰北苑6-703')
    ret = IOLoop.current().run_sync(f)
    print("async_get_coordinates: %s, %s" % (ret[1], ret[0]))

    f = partial(async_get_coordinates, '', '', '杭州市滨江区时代大道南环路口')
    ret = IOLoop.current().run_sync(f)
    print("async_get_coordinates: %s, %s" % (ret[1], ret[0]))
