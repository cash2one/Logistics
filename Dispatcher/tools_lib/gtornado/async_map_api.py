# coding=utf-8
# __author__ = 'mio'
from tornado import gen
from tornado.log import app_log

from tools_lib.gedis.gedis import Redis
from tools_lib.gtornado.baidumap_api import async_get_distance as baidu_get_distance
from tools_lib.gtornado.amap_api import amap_get_distance

from tools_lib.geo.mercator import Mercator


redis_client = Redis()

key_baidu_cal_timeout = "order:cal_distance:baidu_timeout"
key_amap_cal_timeout = "order:cal_distance:amap_timeout"


def cal_straight_distance(from_longitude, from_latitude, to_longitude, to_latitude):
    """
    计算直线距离
    :param from_longitude:
    :param from_latitude:
    :param to_longitude:
    :param to_latitude:
    :return:
    """
    # 百度被限制，计算直线距离

    distance = Mercator.distance(
        float(from_longitude), float(from_latitude),
        float(to_longitude), float(to_latitude)
    )
    app_log.info(">>>>>>>> cal straight distance without baidu <<<<<<<<")
    #  直线距离乘以系数
    return int(1.5 * distance)


@gen.coroutine
def async_get_distance(from_lng, from_lat, to_lng, to_lat):
    if redis_client.exists(key_baidu_cal_timeout) is False:
        # 百度计算距离接口
        order_distance = yield baidu_get_distance(from_lat, from_lng, to_lat, to_lng, '杭州', '杭州', '杭州')
        cal_distance_by = "CALL"
        if order_distance is False:
            # 如果百度接口超时、被限制
            # 不使用百度接口，使用直线距离计算, minute
            order_distance = cal_straight_distance(from_lng, from_lat, to_lng, to_lat)
            set_timeout_redis(key_baidu_cal_timeout)
            cal_distance_by = "CALLWB"
    elif redis_client.exists(key_amap_cal_timeout) is False:
        # 高德接口
        order_distance, rst = yield amap_get_distance(from_lng, from_lat, to_lng, to_lat)
        cal_distance_by = "CALLAMAP"
        if rst == 'timeout':
            order_distance = cal_straight_distance(from_lng, from_lat, to_lng, to_lat)
            cal_distance_by = "CALLWB"
            set_timeout_redis(key_amap_cal_timeout)
    else:
        order_distance = cal_straight_distance(from_lng, from_lat, to_lng, to_lat)
        cal_distance_by = "CALLWB"
    app_log.info(">>>D>>> call distance by {}, distance: {} <<<D<<<".format(cal_distance_by, order_distance))
    raise gen.Return((order_distance, cal_distance_by))


def set_timeout_redis(key, suspended_seconds=600):
    redis_client.set(key, 'fuck')
    redis_client.expire(key, suspended_seconds)
