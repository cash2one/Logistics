#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-09-07 15:19:48
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo
import sys

import arrow
from schema import Schema, SchemaError, And, Optional
from tornado import gen

# from tools_lib.das_api import get_man_info_from_token
from tools_lib.gtornado.escape import schema_utf8, schema_datetime, schema_float
from tools_lib.gtornado.web import executor
from tools_lib.gtornado.web2 import ManHandler
from multiprocessing.dummy import Pool
from tools_lib.java_account import AsyncAccount

from utils import mongodb_router, mongo_client

reload(sys)
sys.setdefaultencoding("utf-8")

pool = Pool(4)


class GPSHandler(ManHandler):
    # @gen.coroutine
    # def get_man_info_from_token_403(self):
    #     """
    #     {
    #         "status": "STATUS_WORKING",
    #         "tel": "13245678901",
    #         "name": "测试3号",
    #         "job_description": [],
    #         "man_id": "56c2e7d97f4525452c8fc23c",
    #         "avatar": "AF9650D87988D915577E4130422187CE"
    #     }
    #     """
    #     try:
    #         token = self.request.headers.get("Authorization")
    #         man_info = yield AsyncAccount.get_user_info_from_token(token)
    #     except Exception as e:
    #         self.resp_forbidden("Can't get token; {}".format(e.message))
    #         raise gen.Return(None)
    #     if not man_info:
    #         self.resp_forbidden("can't get man_info")
    #         return
    #     raise gen.Return(man_info)
    #
    # @gen.coroutine
    # def prepare(self):
    #     # 客户端有闪退的问题, 暂时先把这个报错返回改成403
    #     self.man_info = yield self.get_man_info_from_token_403()

    @gen.coroutine
    def post(self):
        """
            @api {post} /gps/ps/multi 保存风先生实时上传的gps坐标
            @apiVersion 0.1.0
            @apiName ps_get
            @apiGroup app_gps
            @apiDescription 将风先生的gps上传到的mongodb中

            @apiParam (body params) {Double} lng 经度坐标
            @apiParam (body params) {Double} lat 纬度坐标
            @apiParam (body params) {number} time 时间戳，utc, 若为空则是服务器utc时间
            @apiParam (body params) {String} city_code 所在城市code, 用来分表

            @apiParamExample {json} gps_info 参数说明
            [
                {
                    "lng": "120.220654",
                    "lat": "30.220248",
                    "time": "2015-04-12T03:54:47Z",
                    "city_code": "0000000001"
                },
            ]

            @apiSuccess (200) {number} code 200

        """
        try:
            data = Schema(And(
                [
                    {
                        'city_code': schema_utf8,
                        Optional("time"): schema_datetime,
                        "lng": schema_float,
                        "lat": schema_float,
                    },
                ],
                len
            )
            ).validate(self.get_body_args())
        except (SchemaError, Exception):
            self.resp_args_error()
            return

        time = arrow.utcnow().datetime

        def cluster(d):
            client = mongodb_router(d['city_code'], time)
            client.insert({
                "create_time": time,
                "city_code": d['city_code'],
                "man": self.man_info,
                "loc": {
                    "type": "Point",
                    "coordinates": [last['lng'], last['lat']]
                }
            })

        last = data[-1]
        client = mongo_client['gps']['latest']
        client.update(
            {
                "man.id": self.man_info['id'],
            },
            {
                "create_time": time,
                "city_code": last['city_code'],
                "man": self.man_info,
                "loc": {
                    "type": "Point",
                    "coordinates": [last['lng'], last['lat']]
                }
            },
            upsert=True
        )

        pool.map(cluster, data)

        self.resp()
