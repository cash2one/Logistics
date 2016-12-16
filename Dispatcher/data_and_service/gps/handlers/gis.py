#! #!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-09-07 15:19:48
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo
import logging

from schema import Schema, Optional

from handlers.utils import mongo_client, mongodb_router
from tools_lib.gmongoengine.utils import field_to_json_no_round
from tools_lib.gtornado.escape import schema_utf8, schema_date
from tools_lib.gtornado.web2 import ReqHandler

from pymongo import ASCENDING


class LatestHandler(ReqHandler):
    def get(self):
        """
            @api {post} /gps/gis/latest 获取最新的所有的GPS
            @apiVersion 0.1.0
            @apiName gis_latest
            @apiGroup fe_gps
            @apiDescription 获取最新的所有的GPS

            @apiParamExample 请求参数描述

            city_code: (string) 城市代码
            man.id: (string)人的账户id

            @apiSuccessExample {json} gps_info 参数说明
            [
                {
                    "loc": {
                        "type": "Point",
                        "coordinates": [
                            120.22,
                            30.22
                        ]
                    },
                    "create_time": "2016-06-01T08:01:49Z",
                    "city_code": "179",
                    "man": {
                        "tel": "13245678901",
                        "id": "56c2e7d97f4525452c8fc23c",
                        "m_type": "parttime",
                        "name": "测试1号"
                    }
                }
            ]

            @apiSuccess (200) {number} code 200

        """
        try:
            data = Schema({
                Optional("city_code"): schema_utf8,
                Optional("man.id"): schema_utf8
            }).validate(self.get_query_args())
        except Exception as e:
            logging.exception(e.message)
            return

        conn = mongo_client['gps']['latest']

        def pack(doc):
            packed = {}
            for field in doc:
                if field == "_id":
                    continue
                packed[field] = field_to_json_no_round(doc[field])
            return packed

        content = [pack(_) for _ in conn.find(data)]
        self.resp(content=content)


class PathHandler(ReqHandler):
    def get(self):
        """
            @api {post} /gps/gis/path 获取某个人一天的路径
            @apiVersion 0.1.0
            @apiName gis_path
            @apiGroup fe_gps
            @apiDescription 获取某个人一天的路径

            @apiParam (body params) {string} city_code 城市code
            @apiParam (body params) {string} man_id 人员ID
            @apiParam (body params) {string} date

            @apiParamExample {json} gps_info 参数说明
            [
                {
                    "loc": [
                        120.221164,
                        30.220303
                    ],
                    "time": "2016-06-02T07:20:59Z"
                },
                {
                    "loc": [
                        120.22104,
                        30.220311
                    ],
                    "time": "2016-06-02T07:21:31Z"
                },
            ]

            @apiSuccess (200) {number} code 200

        """
        try:
            data = Schema({
                "city_code": schema_utf8,
                "man_id": schema_utf8,
                "date": schema_date
            }).validate(self.get_query_args())
        except Exception as e:
            logging.exception(e.message)
            return

        def pack(doc):
            packed = {}
            packed['loc'] = doc['loc']['coordinates']
            packed['time'] = field_to_json_no_round(doc['create_time'])
            return packed

        conn = mongodb_router(data['city_code'], data['date'])
        result = conn.find({
            "man.id": data['man_id']
        }).sort([("create_time", ASCENDING)])

        content = [pack(_) for _ in result]

        self.set_header('X-Resource-Count', len(content))

        self.resp(content=content)
