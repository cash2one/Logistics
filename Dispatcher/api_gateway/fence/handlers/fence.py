# coding=utf-8

import platform

from tools_lib.gtornado import apis
from tools_lib.gtornado.web import AGRequestHandler
from tools_lib.gtornado.web2 import ManHandler
from tools_lib.host_info import (LOCALHOST_NODE, DEV_OUTER_IP, DEV_NODE, PROD_BL_DAS_PORT, PROD_API_INNER_IP,
                                 PROD_API_NODE)
from tornado.gen import coroutine
from tornado.httpclient import HTTPRequest
from tornado.httputil import url_concat
from tools_lib.java_account import AsyncAccount

if platform.node() in (LOCALHOST_NODE, DEV_NODE):
    ip = DEV_OUTER_IP
elif platform.node() == PROD_API_NODE:
    ip = PROD_API_INNER_IP
else:
    ip = "127.0.0.1"


class FenceHandler(AGRequestHandler):
    """
    栅栏增删查改
    """
    url_with_suffix = "http://%s:{port}/schedule/logic/fence/{obj_id}" % ip
    url = "http://%s:{port}/schedule/logic/fence" % ip

    @coroutine
    def get(self, fence_id=None):
        """
        @api {get} /schedule/fe/fence[/:fence_id] 获取栅栏信息
        @apiName getFenceInfo
        @apiGroup FE_FENCE
        @apiDescription 获取某个栅栏的信息,如果省略ID,则返回栅栏列表
        @apiVersion 0.1.0

        @apiParam (query PARAMETERS) integer page 页码,默认1
        @apiParam (query PARAMETERS) integer count 每页数目,默认100

        @apiSuccessExample 指定fence_id获取单个栅栏
            HTTP/1.1 200
            {
                "content": {
                    "points": [
                    [
                        [
                            120.18857,
                            30.378313
                        ],
                        [
                            120.183683,
                            30.359119
                        ],
                        [
                            120.213579,
                            30.367844
                        ],
                        [
                            120.213867,
                            30.379808
                        ],
                        [
                            120.18857,
                            30.378313
                        ]
                    ]
                    ],
                    "id": "567d0f36f10f5b7955322183",
                    "loc": {
                        "address": "货车地址",
                        "lat": 0,
                        "lng": 0
                    },
                    "name": "半山",
                    "color": "#ffffff" // 显示颜色,默认""
                },
                "message": "",
                "error_code": 0
            }

        @apiSuccessExample 获取全部
        {
          "content": [
            {
              "points": [
                [
                  [
                    117.791747,
                    26.942912
                  ],
                  [
                    116.20958,
                    23.222222
                  ],
                  [
                    121.17685,
                    20.838439
                  ],
                  [
                    124.819515,
                    23.89531
                  ],
                  [
                    120.404164,
                    24.631441
                  ],
                  [
                    117.791747,
                    26.942912
                  ]
                ]
              ],
              "id": "56839950f10f5b0b2819dcbd",
              "loc": {
                "address": "货车地址",
                "lat": 0,
                "lng": 0
              },
              "name": "",
              "color": "#ffffff" // 显示颜色,默认""
            },
            {
              "points": [
                [
                  [
                    117.313418,
                    32.440076
                  ],
                  [
                    114.811385,
                    39.154634
                  ],
                  [
                    117.681364,
                    38.867555
                  ],
                  [
                    117.313418,
                    32.440076
                  ]
                ]
              ],
              "id": "5683939cf10f5b0b2819dcb8",
              "loc": {
                "address": "货车地址",
                "lat": 0,
                "lng": 0
              },
              "name": "北京",
              "color": "#ffffff" // 显示颜色,默认""
            },
            {
              "points": [
                [
                  [
                    120.18857,
                    30.378313
                  ],
                  [
                    120.183683,
                    30.359119
                  ],
                  [
                    120.213579,
                    30.367844
                  ],
                  [
                    120.213867,
                    30.379808
                  ],
                  [
                    120.18857,
                    30.378313
                  ]
                ]
              ],
              "id": "567d0f36f10f5b7955322183",
              "loc": {
                "address": "货车地址",
                "lat": 0,
                "lng": 0
              },
              "name": "半山",
              "color": "#ffffff" // 显示颜色,默认""
            }
          ],
          "message": "",
          "error_code": 0
        }
        """
        if fence_id:
            req = HTTPRequest(self.url_with_suffix.format(port=PROD_BL_DAS_PORT, obj_id=fence_id), method="GET")
        else:
            page = self.get_query_argument("page", 1)
            count = self.get_query_argument("count", 100)

            req = HTTPRequest(url_concat(self.url.format(port=PROD_BL_DAS_PORT), {
                "page": page,
                "count": count,
                "limit": 0
            }), method="GET")
        yield self.redirect_request(req)

    @coroutine
    def post(self):
        """
        @api {post} /schedule/fe/fence 新建栅栏
        @apiName createFence
        @apiGroup FE_FENCE
        @apiDescription 创建一个新栅栏
        @apiVersion 0.1.0

        @apiParamExample Request-Example
            {
                "name": "栅栏名",
                "points": [[
                    [12,12], ... // 节点
                ]],
                "loc": {
                    "address": "货车地址",
                    "lat": 0,
                    "lng": 0
                },
                "color": "#ffffff" // 显示颜色,默认""
            }
        """
        req = HTTPRequest(self.url.format(port=PROD_BL_DAS_PORT), method="POST", body=self.request.body)
        yield self.redirect_request(req)

    @coroutine
    def patch(self, fence_id):
        """
        @api {patch} /schedule/fe/fence/:fence_id 栅栏修改
        @apiName modifyFence
        @apiGroup FE_FENCE
        @apiDescription 更改栅栏信息
        @apiVersion 0.1.0

        @apiParamExample Request-Example
            {
                "name": "栅栏名",
                "points": [[
                    [12,12], ... // 节点
                ]],
                "loc": {
                    "address": "货车地址",
                    "lat": 0,
                    "lng": 0
                },
                "color": "#ffffff", // 显示颜色,默认""
                "manager": {
                    "name": "XXX",
                    "tel": "15200000"
                }
            }
        """
        req = HTTPRequest(self.url_with_suffix.format(port=PROD_BL_DAS_PORT, obj_id=fence_id), method="PATCH",
                          body=self.request.body)
        yield self.redirect_request(req)

    @coroutine
    def delete(self, fence_id):
        """
        @api {delete} /schedule/fe/fence/:fence_id 删除栅栏
        @apiName deleteFence
        @apiGroup FE_FENCE
        @apiDescription 删除栅栏
        @apiVersion 0.1.0

        """
        req = HTTPRequest(self.url_with_suffix.format(port=PROD_BL_DAS_PORT, obj_id=fence_id), method="DELETE")
        yield self.redirect_request(req)


class FencePointCompareHandler(AGRequestHandler):
    @coroutine
    def post(self):
        """
        @api {post} /schedule/fe/fence/point_cmp 寻找一点经纬度落入的栅栏
        @apiName PointCompare
        @apiGroup FE_FENCE
        @apiDescription 查找点落入的栅栏
        @apiVersion 0.1.0

        @apiParam (BODY PARAMETERS) {array} point 点经纬度

        @apiParamExample Request-Example
            {
                "point": [12,12]
            }

        @apiSuccessExample 返回
        {
            "content": [
                {
                    "loc": {},
                    "name": "-西湖3 -ZS浙大紫金港",
                    "color": "#ffa611",
                    "manager": {
                        "tel": "18067963549",
                        "name": "刘从志"
                    },
                    "points": [
                        [
                            [120.104606, 30.325150999999998], ...
                        ]
                    ],
                    "create_time": "2016-01-06T13:39:25Z",
                    "id": "568d190df10f5b15c1c983c8"
                }
            ],
            "message": "",
            "error_code": 0
        }
        """
        url = "http://{ip}:{port}/schedule/logic/fence/point_cmp".format(ip=ip, port=PROD_BL_DAS_PORT)
        req = HTTPRequest(url.format(port=PROD_BL_DAS_PORT), method="POST", body=self.request.body)
        yield self.redirect_request(req)


class IfInsideFenceHandler(AGRequestHandler):
    @coroutine
    def post(self):
        """
        @api {post} /schedule/fe/fence/inout 区分一列点落入和未落入栅栏
        @apiName IfPointInsideFence
        @apiGroup FE_FENCE
        @apiDescription 查找点落入的栅栏,返回落入栅栏和未落入的点
        @apiVersion 0.1.0

        @apiParam (BODY PARAMETERS) {array} point_list 点经纬度列表

        @apiParamExample Request-Example
            {
                "point_list": [
                    [12,12], ... // 点
                ]
            }

        @apiSuccessExample 指定fence_id获取单个栅栏
            HTTP/1.1 200
            {
                "content": {
                    "in": [ // 落入任何栅栏的点列表
                        [
                            120.18857,
                            30.378313
                        ],
                        [
                            120.183683,
                            30.359119
                        ]
                    ],
                    "out":[ // 未落入任何栅栏的点列表
                        [
                            120.213579,
                            30.367844
                        ],
                        [
                            120.213867,
                            30.379808
                        ],
                        [
                            120.18857,
                            30.378313
                        ]
                    ]
                },
                "message": "",
                "error_code": 0
            }
        """
        url = "http://{ip}:{port}/schedule/logic/fence/point_inout".format(ip=ip, port=PROD_BL_DAS_PORT)
        req = HTTPRequest(url.format(port=PROD_BL_DAS_PORT), method="POST", body=self.request.body)
        yield self.redirect_request(req)


class ManagerHandler(ManHandler):
    @coroutine
    def get(self):
        """
        获取围栏管理员
        """
        dm_familiar_points = yield AsyncAccount.familiar_points(self.man_info["id"])
        fence_managers_list = yield apis.query_fence_manager(dm_familiar_points)
        fence_managers_dict = {i["tel"]: i["name"] for i in fence_managers_list}
        self.resp({
            "fence_managers": [
                {
                    "tel": i,
                    "name": fence_managers_dict[i]
                } for i in fence_managers_dict.keys()
                ]
        })
