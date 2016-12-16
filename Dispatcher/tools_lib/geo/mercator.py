#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-06-30 19:40:25
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo

import math


def validate_lng(lng):
    if lng > 180 or lng < -180:
        return False
    return True


def validate_lat(lat):
    if lat > 90 or lat < -90:
        return False
    return True


class Mercator(object):
    M = 20037508.342789

    @classmethod
    def lnglat2mercator(cls, lng, lat):
        if not validate_lng(lng) or not validate_lat(lat):
            return (0, 0)
        x = (lng * cls.M) / 180
        y = math.log(math.tan(((90 + lat) * math.pi / 360))) / (math.pi / 180)
        y = y * cls.M / 180
        return (x, y)

    @classmethod
    def mercator2lnglat(cls, x, y):
        try:
            lng = x / cls.M * 180
            lat = y / cls.M * 180
            lat = (180 / math.pi) * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
            if not validate_lng(lng) or not validate_lat(lat):
                return (0, 0)
            return (lng, lat)
        except Exception:
            return (0, 0)

    @classmethod
    def distance(cls, from_lng, from_lat, to_lng, to_lat):

        if not validate_lat(from_lat) and not validate_lat(to_lat) or \
                not validate_lng(from_lng) or not validate_lng(to_lng):
            return -1

        lng1, lat1 = cls.lnglat2mercator(from_lng, from_lat)
        lng2, lat2 = cls.lnglat2mercator(to_lng, to_lat)

        x = (lng1 - lng2) ** 2
        y = (lat1 - lat2) ** 2
        distance = math.sqrt(x + y)
        return distance
