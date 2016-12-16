#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-09-07 15:19:48
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo

import re

import arrow
import datetime
from schema import And, Use, Or, Optional
from tornado.escape import utf8, to_unicode


def power_split(value, separator=',', schema=str):
    assert callable(schema)
    value = utf8(value)
    value = value.strip()
    l = re.split("\s*" + separator + "\s*", value)  # 这个slip直接去除逗号左右的空格
    return [v for v in l if v != '']


schema_utf8_multi = And(Use(utf8), Use(lambda x: [_.strip() for _ in x.split(',') if _ != ""]))
schema_unicode_multi = And(Use(utf8), Use(lambda x: [to_unicode(_.strip()) for _ in x.split(',') if _ != ""]))
schema_utf8 = And(Use(utf8), len)
schema_utf8_empty = Use(utf8)  # 允许为空的utf8
schema_unicode = And(Use(to_unicode), len)
schema_unicode_empty = Use(to_unicode)
schema_unicode_upper = And(Use(utf8), len, Use(str.upper), Use(lambda x: x.decode('utf-8')))
schema_int = Use(int)
schema_float = And(Use(float), Use(lambda x: round(x, 10)))
schema_float_empty = And(Use(lambda x: 0 if x == '' else x), schema_float)
schema_float_2 = And(Use(float), Use(lambda x: round(x, 2)))
# schema_fh_base = And(Use(float), Use(lambda x: round(x, 2)), lambda x: 0 < x < 100)
schema_bool = And(Use(int), Use(bool))
schema_objectid = And(schema_unicode, lambda x: len(x) == 24)
schema_date = And(Use(utf8), Use(arrow.get), Use(lambda x: x.date()))
schema_datetime = And(Use(utf8), Use(arrow.get), Use(lambda x: x.datetime))
schema_hhmm = And(Use(utf8), Use(lambda x: datetime.time(*map(int, x.split(':')))), Use(lambda x: x.strftime("%H:%M")))

schema_operator = {
    "id": schema_utf8,
    "name": schema_utf8_empty,
    "tel": schema_utf8,
    "m_type": schema_utf8_empty,
    Optional(object): object
}
schema_receiver = {
    "name": schema_utf8_empty,
    "tel": schema_utf8_empty,
    "addr": schema_utf8_empty,
    "lat": Use(float),
    "lng": Use(float),
    Optional(object): object,
}

schema_operator_unicode = {
    u"id": schema_unicode,
    u"name": schema_unicode_empty,
    u"tel": schema_unicode,
    u"m_type": schema_unicode_empty,
    Optional(object): object
}
schema_node_x_unicode = {
    u'name': schema_unicode_empty,
    u'tel': schema_unicode_empty,

    u'addr': schema_unicode_empty,
    u'lat': schema_float,
    u'lng': schema_float,
    u'fence': {u'id': schema_unicode, u'name': schema_unicode_empty, Optional(object): object},
}
schema_shop_unicode = {
    u'id': schema_unicode,
    u'name': schema_unicode_empty,
    u'tel': schema_unicode,
    u'm_type': schema_unicode_empty,

    u'lat': schema_float,
    u'lng': schema_float,
    Optional(u'address'): schema_unicode_empty
}
schema_loc = {
    u"lat": schema_float,
    u"lng": schema_float,
    Optional(u"addr"): schema_utf8_empty
}
