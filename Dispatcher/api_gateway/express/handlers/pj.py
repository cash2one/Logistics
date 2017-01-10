# coding: utf-8


import json
import arrow
import logging

from .apis import express, rewards, settlement
from .apis import node
from schema import Schema, Optional, And, SchemaError
from tools_lib import java_windlog
from tools_lib.bl_expr import ExprState
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.gtornado import http_code
from tools_lib.gtornado.baidumap_api import async_get_coordinates
from tools_lib.gtornado.escape import schema_loc
from tools_lib.gtornado.escape import (schema_unicode_empty, schema_unicode, schema_unicode_multi, schema_float_2,
                                       schema_date, schema_utf8, schema_int, schema_bool, schema_utf8_multi)
from tools_lib.gtornado.web2 import ManHandler
from tornado.gen import coroutine


class ReceiverHandler(ManHandler):
    @coroutine
    def patch(self, number):
        """
        @apiIgnore
        @api {patch} /express/pj/single/{number}/receiver 派件端 - 派件员为商户补全信息+定价
        @apiVersion 0.0.1
        @apiName pj_express_receiver
        @apiGroup app_pj


        @apiParam (query param) {String} number 订单编号
        @apiParam (body param) {String} address 地址
        @apiParam (body param) {String} name 收件人姓名
        @apiParam (body param) {String} tel 收件人电话
        @apiParam (body param) {String} [remark] 运单备注
        @apiParam (body param) {float}  weight 物品重量

        @apiParamExample {json} 请求示例
        patch http://api.gomrwind.com:5000/express/pj/single/000001000333/receiver
        {
            "tel": "12345678901"
            "address": "星耀城"
            "name": "王先生"
            "remark": "尽快送货",
            "weight": 2.5  // 如果是2-2.5kg,传入2.5
        }

        """
        try:
            kw = Schema({
                "address": schema_unicode,
                "name": schema_unicode_empty,
                "tel": schema_unicode,
                Optional("remark"): schema_unicode_empty,
                # "weight": schema_float
            }).validate(self.get_body_args())
        except Exception as e:
            logging.exception(e.message)
            self.resp_args_error()
            return

        address = kw.pop("address")
        name = kw.pop("name")
        tel = kw.pop("tel")

        # 解析收方地址, 获取对应的围栏
        lng, lat = yield async_get_coordinates("", "", address)
        fence = yield node.query_fence_point_within([lng, lat])

        kw.update({
            "node_n": {
                "name": name,
                "tel": tel,
                "addr": address,
                "lng": lng,
                "lat": lat,
                "fence": fence
            },
            "operator": self.man_info,
        })

        yield self.resp_redirect(express.redirect_modify_receiver(number, kw))


class FilledExpressHandler(ManHandler):
    @coroutine
    def get(self):
        """
        @api {get} /express/pj/multi/empty 派件端 - 去收件时获取商户运单
        @apiVersion 0.0.1
        @apiName pj_express_empty
        @apiGroup app_pj

        @apiParam (query param) {String} creator_id 商户id

        """
        self.resp_forbidden('这个接口已经关闭, 不能给你们调用啦')
        return
        try:
            params = Schema({
                "creator_id": schema_unicode,
                Optional('page', default=1): schema_int,
                Optional('count', default=20): schema_int,
                Optional('only', default=['status', 'number', 'fee', 'node', 'id']): schema_unicode_multi,
            }).validate(self.get_query_args())
        except SchemaError:
            self.resp_args_error()
            return

        # 1. 定制列表查询条件: 取商户待领取运单列表(没被发起过收款的)
        query = {
            "status__sub_status": ExprState.STATUS_PRE_CREATED,
            'assignee__exists': False,  # 未被领取
            "creator__id": params['creator_id'],
            'page': params['page'],
            'count': params['count'],
            'only': params['only'],
            'order_by': ['node.node_n.tel', '-number'],
        }
        resp_expr_obj = yield self.async_fetch(express.redirect_pickle_search(query))
        resp_expr_list = resp_expr_obj.content

        # 2. 计算我应该要提醒该商户支付的运费
        pipeline = [
            # 取待配送员定价收件的运单列表
            {
                "$match": {
                    "creator.id": params['creator_id'],  # 是该商户下的单
                    "status.sub_status": ExprState.STATUS_PRE_CREATED,  # 商户刚下单, 还没批量定过价呢
                    "assignee.id": self.man_info['id'],  # 是我领取的单
                    "fee.fh": {"$exists": True, "$ne": None}
                }
            },
            # 加一下, 获得自己收件的这个商户总计待支付的运费
            {
                "$group": {
                    "_id": None,
                    "cash": {"$sum": "$fee.fh"},
                    "number_list": {"$addToSet": '$number'}  # 已领x单
                }
            }
        ]
        resp_cash_obj = yield self.async_fetch(express.redirect_aggregation(pipeline=pipeline))
        resp_cash = 0 if not resp_cash_obj.content else resp_cash_obj.content[0]['cash']
        resp_number_list = [] if not resp_cash_obj.content else resp_cash_obj.content[0]['number_list']

        self.set_header('X-Resource-Count', resp_expr_obj.headers['X-Resource-Count'])
        self.resp({'expr_list': resp_expr_list, 'cash': resp_cash, 'number_list': resp_number_list})


class AssignToMe(ManHandler):
    @coroutine
    def patch(self):
        self.resp_forbidden('该接口关闭啦, 不能调用啦')
        return

        try:
            kw = Schema({
                'number': schema_unicode
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error()
            return
        # 只是去改一下assignee
        kw['operator'] = self.man_info
        yield self.resp_redirect(express.redirect_assign_to_me(kw))

    @coroutine
    def get(self):
        self.resp_forbidden('该接口已关闭, 不能给你们调用啦')
        return
        try:
            params = Schema({
                Optional('creator_id'): schema_unicode,
                Optional('page', default=1): schema_int,
                Optional('count', default=20): schema_int,
                Optional('only', default=['status', 'number', 'fee', 'node', 'id']): schema_unicode_multi,
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        # == 确认运单-发起收款页面
        if 'creator_id' in params:
            # 1. 定制列表查询条件: 取我领取了的运单列表
            query = {
                'status__sub_status': ExprState.STATUS_PRE_CREATED,  # 没被发起过收款
                'assignee__id': self.man_info['id'],  # 被我领取
                'creator__id': params['creator_id'],  # 是这个商户的
                'page': params['page'],
                'count': params['count'],
                'only': params['only'],
                'order_by': ['-number'],
            }
            resp_expr_obj = yield self.async_fetch(express.redirect_pickle_search(query))
            resp_expr_list = resp_expr_obj.content

            # 2. 计算我应该要提醒该商户支付的运费
            pipeline = [
                # 取待配送员定价收件的运单列表
                {
                    "$match": {
                        "creator.id": params['creator_id'],  # 是该商户下的单
                        "status.sub_status": ExprState.STATUS_PRE_CREATED,  # 还没发起过收款呢
                        "assignee.id": self.man_info['id'],  # 是我领取的单
                        "fee.fh": {"$exists": True, "$ne": None}
                    }
                },
                # 加一下, 获得自己收件的这个商户总计待支付的运费
                {
                    "$group": {
                        "_id": None,
                        "cash": {"$sum": "$fee.fh"},
                        "number_list": {"$addToSet": '$number'}  # 已领x单
                    }
                }
            ]
            resp_cash_obj = yield self.async_fetch(express.redirect_aggregation(pipeline=pipeline))
            resp_cash = 0 if not resp_cash_obj.content else resp_cash_obj.content[0]['cash']
            resp_number_list = [] if not resp_cash_obj.content else resp_cash_obj.content[0]['number_list']

            self.set_header('X-Resource-Count', resp_expr_obj.headers['X-Resource-Count'])
            self.resp({'expr_list': resp_expr_list, 'cash': round(resp_cash, 2), 'number_list': resp_number_list})
            return
        # == 待收件-立即查看-寄方列表(带单数)
        else:
            pipeline = [
                # 取待配送员领取/代客户填单的运单列表
                {
                    '$match': {
                        "status.sub_status": ExprState.SUB_STATUS_PRE_CREATED,  # 还没发起过收款呢
                        "assignee.id": self.man_info['id'],  # 是我领取的单
                        "fee.fh": {"$exists": True, "$ne": None}
                    }
                },
                # 加一下, 获得自己收件的这个商户总计待支付的运费
                {
                    '$group': {
                        '_id': '$creator.id',
                        'shop_id': {'$first': '$creator.id'},
                        'name': {'$first': '$creator.name'},
                        "expr_count": {"$sum": 1},
                        "cash": {"$sum": "$fee.fh"},
                    }
                },
                # 获得所有expr_count的sum
                {
                    '$project': {
                        '_id': 0,
                        'shop_id': 1,
                        'name': 1,
                        'expr_count': 1,
                        'cash': 1,
                    }
                }
            ]
            resp_obj = yield self.async_fetch(express.redirect_aggregation(pipeline=pipeline))
            expr_count_sum = sum([o['expr_count'] for o in resp_obj.content])
            self.set_header('X-Resource-Count', expr_count_sum)
            self.resp(resp_obj.content)
            return


class MultiPricing(ManHandler):
    @coroutine
    def patch(self):
        try:
            kw = Schema({
                "shop_id": schema_unicode,
                "cash": schema_float_2,
                "number_list": [
                    schema_unicode
                ]
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e)
            self.resp_args_error(content=e.message)
            return
        kw['operator'] = self.man_info
        yield self.resp_redirect(express.redirect_multi_pricing(kw))


class SingleExpressHandler(ManHandler):
    @coroutine
    def patch(self, number):
        """
        @api {PATCH} /express/pj/single/{number} 派件端 - 妥投
        @apiName pj_express_single_patch
        @apiGroup app_pj
        @apiVersion 0.0.1

        @apiParam (query param) {string} number 运单号
        @apiParam (body param) {string} [msg] 附加信息

        @apiParamExample {json} 请求示例
        patch http://api.gomrwind.com:5000/express/pj/single/000001000333
        {
            "tel": "12345678901"
            "msg": "取件啦"
            "operating_loc": {
                "lat":
                "lng":
                "addr": "地址信息"
            }
        }
        @apiUse bad_response
        """
        try:
            data = Schema({
                "tel": schema_unicode,
                "msg": schema_unicode_empty,
                Optional("operating_loc", default={}): schema_loc
            }).validate(self.get_body_args())
        except Exception:
            self.resp_args_error()
            return
        operator = self.man_info
        operator["operating_loc"] = data["operating_loc"]
        # 1. 执行妥投
        resp_obj = yield self.async_fetch(express.redirect_perform_expr_event(
            number=number,
            operation=ExprState.EVENT_TT,
            operator=operator,
            msg=data["msg"],
            node__node_n__real_tel=data['tel'],
            node__node_n__msg=data['msg']
        ))
        # 2. 数据组log: 妥投
        if http_code.is_success(resp_obj.code):
            try:
                expr = resp_obj.content
                yield java_windlog.log_create(
                    type=21006,
                    creatorId=self.man_info["id"],
                    createTime=arrow.utcnow().isoformat(),
                    orderId=expr["number"],
                    remark=json.dumps(expr["node"]["node_n"], ensure_ascii=False)
                )
            except Exception as e:
                logging.warn(e.message)
        # 3. 不管收件结果如何, 原样返回
        self.resp(content=resp_obj.content, status_code=resp_obj.code)


class ErrorHandler(ManHandler):
    @coroutine
    def get(self, number):
        """
        @api {get} /express/pj/single/{number}/error 派件端 - 异常类型列表
        @apiVersion 0.0.1
        @apiName pj_express_single_error_get
        @apiGroup app_pj


        @apiSuccessExample 成功返回示例
            HTTP/1.1 200 OK
            body:
            [
                {
                    "type": "客户拒收"
                    "reason": [
                        "商品质量问题",
                        "客户取消订单",
                        "货物错误",
                        "货物外包装破损"
                    ],
                },
                ......
            ]


        """
        content = [
            {
                "type": "延迟派件",
                "reason": [
                    "收方要求延期派件",
                    "收方更改配送地址",
                ]
            },
            {
                "type": "收方拒收",
                "reason": [
                    "商品质量问题",
                    "收方已取消订单",
                    "货物错误",
                    "货物外包装破损"
                ],
            },
            {
                "type": "寄方确认取消配送",
                "reason": [
                    "寄方确认取消配送",
                ]
            }
        ]

        self.resp(content=content)

    @coroutine
    def patch(self, number):
        """
        @api {PATCH} /express/pj/single/{number}/error 派件端 - 标记异常
        @apiName pj_express_single_error_patch
        @apiGroup app_pj
        @apiVersion 0.0.1

        @apiParam (query param) {string} number 运单号
        @apiParam (body param) {string} type 附加信息
        @apiParam (body param) {string} reason 附加信息
        @apiParam (body param) {object} operating_loc 地址信息
        @apiParam (body param) {float} operating_loc.lat 纬度
        @apiParam (body param) {float} operating_loc.lng 经度
        @apiParam (body param) {string} operating_loc.addr 地址信息

        @apiUse bad_response
        """
        try:
            data = Schema({
                "type": schema_unicode,
                "reason": schema_unicode_empty,
                Optional("operating_loc", default={}): schema_loc
            }).validate(json.loads(self.request.body))
        except Exception:
            self.resp_args_error()
            return
        operator = self.man_info
        operator["operating_loc"] = data["operating_loc"]

        op = {
            "延迟派件": ExprState.EVENT_DELAY,
            "收方拒收": ExprState.EVENT_REFUSE,
            "寄方确认取消配送": ExprState.EVENT_TRASH,
        }

        operation = op[data['type']]

        yield self.resp_redirect(express.redirect_perform_expr_event(
            number=number,
            operation=operation,
            operator=operator,
            msg=data["reason"],
        ))


class DataExplainHandler(ManHandler):
    @coroutine
    def get(self):
        """
        @api {get} /express/pj/data/explain 派件端 - 数据字段说明
        @apiVersion 0.0.1
        @apiName pj_data_explain
        @apiGroup app_pj


        @apiSuccessExample 成功返回示例
            HTTP/1.1 200 OK
            body:
            [
                {
                    "title": "总计收件？",
                    "description": "从客户处收取的件。",
                    "ps": "",
                },
                ...
            ]

        """
        content = [
            # {
            #     "title": "总计收件？",
            #     "description": "从客户处收取的件",
            #     "ps": "",
            # },
            # {
            #     "title": "总计转交？",
            #     "description": "从客户处收的，且已转交出去的件",
            #     "ps": "注：由自己收且自己派的件，确认妥投后，总计转交会 +1",
            # },
            # {
            #     "title": "总计派件？",
            #     "description": "从其他人处接收的，进行派送的件",
            #     "ps": "注：由自己收且自己派的件，确认妥投后，总计派件会 +1",
            # },
            # {
            #     "title": "总计妥投？",
            #     "description": "已确认妥投的件",
            #     "ps": "注：总计投妥 = 待审核 + 审核通过",
            # },
            {
                "title": "总计收件？",
                "description": "从客户处收的，且已转交出去的件",
                "ps": "",
            },
            {
                "title": "总计派件？",
                "description": "由自己派送的，且已确认妥投的件",
                "ps": "",
            },
        ]
        self.resp(content=content)
