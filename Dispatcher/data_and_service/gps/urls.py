#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .handlers import ps, gis

# 请严格按照顺序来, 不然正则匹配会出错
urls = [
    # 添加GPS
    (r"^/gps/ps/multi$", ps.GPSHandler),

    # 获取最近一条
    (r"^/gps/gis/latest$", gis.LatestHandler),

    # 获取最近一条
    (r"^/gps/gis/path$", gis.PathHandler)

]
