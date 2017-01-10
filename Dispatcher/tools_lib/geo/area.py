# -*- coding:utf-8 -*-
if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.join(os.getcwd(), os.pardir))

from tools_lib.common_util.archived.mysql_tools import Conn2Mysql
from tools_lib.gedis.core_redis_key import *
from tools_lib.gedis.gedis import Redis

redis_client = Redis()


def name2code(province='', city='', district=''):
    """
    中文地理位置编码
    :param province:
    :param city:
    :param district:
    :return:
        {
            "province_code": 3921830921830921,
            "city_code": 8309218309218,
            "district_code": 830921830921
        }
    """
    redis_key = key_area_code.format(province_name=province, city_name=city, district_name=district)
    if redis_client.exists(redis_key):
        result = redis_client.hgetall(redis_key)
        for k in list(result.keys()):
            result[k] = int(result[k])
    else:
        result = {
            "province_code": 0,
            "city_code": 0,
            "district_code": 0,
        }
        with Conn2Mysql() as cn:
            if province and city and district:
                sql = "select code, parent from f_area.area where province like %s and city like %s and district like %s and street = ''"
                rst = cn.get_all(sql, ['%' + province + '%', '%' + city + '%', '%' + district + '%'])
                if rst:
                    result['district_code'] = rst[0]['code']
                    result['city_code'] = rst[0]['parent']
                    sql = "select code, parent from f_area.area where code = %s and parent != 0"
                    rst = cn.get_all(sql, [result['city_code']])
                    if rst:
                        result['province_code'] = rst[0]['parent']
            else:
                if province:
                    sql = "select code from f_area.area where province like %s and city = '' and district = '' and street = ''"
                    rst = cn.get_all(sql, ['%' + province + '%'])
                    if rst:
                        result['province_code'] = rst[0]['code']
                if city:
                    sql = "select code, parent from f_area.area where city like %s and district = '' and street = ''"
                    rst = cn.get_all(sql, ['%' + city + '%'])
                    if rst:
                        result['city_code'] = rst[0]['code']
                        result['province_code'] = rst[0]['parent']
                if district:
                    sql = "select code, parent from f_area.area where district like %s and street = ''"
                    rst = cn.get_all(sql, ['%' + district + '%'])
                    if rst:
                        result['district_code'] = rst[0]['code']
                        result['city_code'] = rst[0]['parent']
                        if result['province_code'] is 0:
                            sql = "select code, parent from f_area.area where code = %s and parent != 0"
                            rst = cn.get_all(sql, [result['city_code']])
                            if rst:
                                result['province_code'] = rst[0]['parent']
    return result


def code2name(province_code=0, city_code=0, district_code=0):
    """
    地理编码逆向解析中文名
    :param province_code:
    :param city_code:
    :param district_code:
    :return:
        {
            "province": "浙江省",
            "city": "杭州市",
            "district": "西湖区",
        }
    """
    result = {
        "province": "",
        "city": "",
        "district": ""
    }
    with Conn2Mysql() as cn:
        if province_code > 0:
            sql = "select province from f_area.area where code = %s"
            rst = cn.get_all(sql, [province_code])
            if rst:
                result['province'] = rst[0]['province']
        if city_code > 0:
            sql = "select province, city from f_area.area where code = %s"
            rst = cn.get_all(sql, [city_code])
            if rst:
                result['province'] = rst[0]['province']
                result['city'] = rst[0]['city']
        if district_code > 0:
            sql = "select province, city, district from f_area.area where code = %s"
            rst = cn.get_all(sql, [district_code])
            if rst:
                result['province'] = rst[0]['province']
                result['city'] = rst[0]['city']
                result['district'] = rst[0]['district']
    return result


if __name__ == '__main__':
    rst = name2code('浙江省', '杭州市', '滨江区')
    print(rst)
    print((code2name(rst['province_code'], rst['city_code'], rst['district_code'])))

