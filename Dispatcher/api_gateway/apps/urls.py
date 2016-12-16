#!/usr/bin/env python
# -*- coding: utf-8 -*-
from handlers import app

# 请严格按照顺序来, 不然正则匹配会出错
urls = [
    # 获取所有app, 以及app删除
    (r"^/apps$", app.AppHandler),
    # 获得当前最新的版本号
    (r"^/apps/version$", app.VersionHandler),
    # 获取下载链接
    (r"^/apps/download$", app.DownloadHandler),
    # 发布新包
    (r"^/apps/release$", app.ReleaseHandler),
    # 查询服务器时间
    (r"^/apps/time/now$", app.TimeHandler),

    # # 支付成功
    # (r"^/apps/charge$", app.ChargeHandler),
    # # 支付成功
    # (r"^/apps/create_charge$", app.CreateChargeHandler),
]
