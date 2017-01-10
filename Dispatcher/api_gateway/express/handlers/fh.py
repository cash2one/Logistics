# coding:utf-8

import arrow
import logging

from .apis import express
from .apis import node
from schema import Schema, Optional, SchemaError, Or
from tools_lib import java_windlog
from tools_lib.bl_expr import ExprState
from tools_lib.gtornado import baidumap_api
from tools_lib.gtornado import http_code
from tools_lib.gtornado.escape import (schema_unicode_empty, schema_unicode, schema_int, schema_float_2, schema_float,
                                       schema_unicode_multi)
from tools_lib.gtornado.web2 import ShopHandler
from tools_lib.pricing import pricing
from tornado.gen import coroutine


class Pricing(ShopHandler):
    @coroutine
    def get(self, fh_or_h5):
        """
        @api {GET} /express/ps/single/pricing 发货端 - 拿计价
        @apiName fh_express_single_get_price
        @apiGroup app_ps

        @apiParam (query param) {float} weight 运单重量
        @apiParam (query param) {int} [volume_a] 运单体积-长
        @apiParam (query param) {int} [volume_b] 运单体积-宽
        @apiParam (query param) {int} [volume_c] 运单体积-高
        :return:
        """
        try:
            params = Schema(
                Or(
                    {
                        'weight': schema_float_2
                    },
                    {
                        "volume_a": schema_int, "volume_b": schema_int, "volume_c": schema_int
                    })).validate(self.get_query_args())
        except SchemaError as e:
            logging.warn(e)
            self.resp_args_error()
            return

        fh_extra, msg, weight_max = pricing(
            volume=params.get('volume_a', 0) * params.get('volume_b', 0) * params.get('volume_c', 0),
            weight=params.get('weight', 0.0))

        self.resp(dict(msg=msg, weight=weight_max, fh_extra=fh_extra, fh=15.0 + fh_extra))


class SingleExpressHandler(ShopHandler):
    @coroutine
    def get(self, fh_or_h5, number):
        """
            @api {get} /express/{ps|fh|h5}/single/{number} 通用 - 查询一个运单详情
            @apiName common_express_single_get
            @apiGroup common_express
            @apiVersion 0.0.1

            @apiParam (query string) {string} [excludes] 去除(不需要的字段,逗号分隔)
            @apiParam (query string) {string} [includes] 包括(需要的字段,逗号分隔)
            @apiParam (query string) {string} [only] 仅(逗号分隔)

            @apiSuccessExample 成功返回示例
            HTTP/1.1 200 OK
            {express}
            @apiUse default_express
            @apiUse bad_response
        """
        qs = self.get_query_args()
        yield self.resp_redirect(express.redirect_get_express(number, **qs))

    @coroutine
    def post(self, fh_or_h5):
        """
            @api {post} /express/{fh|h5}/single 发货端 - 填单发货(发一单)
            @apiName common_express_single_post
            @apiGroup common_express

            @apiParam (body param) {string} sender.addr 运单发货地址
            @apiParam (body param) {string} sender.name 寄方姓名
            @apiParam (body param) {string} sender.tel 寄方电话

            @apiParam (body param) {string} receiver.addr 运单送达地址
            @apiParam (body param) {string} receiver.name 收方姓名
            @apiParam (body param) {string} receiver.tel 收方电话
            @apiParam (body param) {string} [remark] 备注

            @apiSuccessExample 成功返回示例
            HTTP/1.1 200 OK
            {express}
            @apiUse default_express

            @apiUse bad_response
        """
        try:
            kw = Schema({
                "sender": {
                    "addr": schema_unicode,
                    "name": schema_unicode,
                    "tel": schema_unicode,
                    "lat": schema_float,
                    "lng": schema_float,
                },
                "receiver": {
                    "addr": schema_unicode,
                    "name": schema_unicode,
                    "tel": schema_unicode,
                    "lat": schema_float,
                    "lng": schema_float,
                },
                Optional("remark", default=""): schema_unicode_empty
            }).validate(self.get_body_args())
        except SchemaError:
            self.resp_error("请将信息填写完整.")
            return

        sender = kw['sender']
        receiver = kw['receiver']
        # 解析发货人当前位置地址所在围栏 todo: 围栏稳定情况下,可以cache商户所在围栏信息
        # lng_0, lat_0 = yield baidumap_api.async_get_coordinates("", "", kw["sender"]["addr"])
        lng_0, lat_0 = sender['lng'], sender['lat']
        shop_fence = yield node.query_fence_point_within([lng_0, lat_0])
        if shop_fence['id'] == 'x':
            self.resp_error('发货地址的经纬度不在服务范围内哦.')
            return
        # 解析送达地址所在围栏
        # lng_n, lat_n = yield baidumap_api.async_get_coordinates("", "", kw["receiver"]["addr"])
        lng_n, lat_n = receiver['lng'], receiver['lat']
        receiver_fence = yield node.query_fence_point_within([lng_n, lat_n])
        if receiver_fence['id'] == 'x':
            self.resp_error('送达地址的经纬度不在服务范围内哦.')
            return

        expr_to_create = {
            # "remark": kw["remark"],
            "node": {
                # 寄方地址
                "node_0": {
                    "name": kw['sender']['name'],
                    "tel": kw['sender']['tel'],
                    "addr": kw['sender']['addr'],
                    "lng": lng_0,
                    "lat": lat_0,
                    "fence": shop_fence
                },
                # 送达地址
                "node_n": {
                    "name": kw['receiver']["name"],
                    "tel": kw['receiver']["tel"],
                    "addr": kw['receiver']["addr"],
                    "lng": lng_n,
                    "lat": lat_n,
                    "fence": receiver_fence
                }
            },
            "fee": {}
        }
        creator_info = {
            "id": self.shop_info["id"],
            "name": self.shop_info.get("name", ""),
            "tel": self.shop_info["tel"],
            "m_type": self.get_app_name(),
            "lat": self.shop_info['lat'],
            "lng": self.shop_info['lng']
        }
        resp = yield self.async_fetch(express.redirect_bulk_create_express(
            creator=creator_info,
            expr_list=[expr_to_create],
            pay=False
        ))
        self.resp_created(resp.content[0])

    @coroutine
    def delete(self, fh_or_h5, number):
        """
            @api {delete} /express/{fh|h5}/single 发货端 - 取消运单
            @apiName common_express_single_delete
            @apiGroup common_express
            @apiVersion 0.0.1

            @apiParam (query param) {string} number 运单号
            @apiSuccessExample 成功返回示例
            HTTP/1.1 201 CREATED
            {express}
            @apiUse default_express

        """
        data = self.get_body_args()
        yield self.resp_redirect(express.redirect_perform_expr_event(
            number,
            operation=ExprState.EVENT_CANCEL,
            operator=self.shop_info,
            msg=data.get("msg", "")
        ))


class Call(ShopHandler):
    @coroutine
    def post(self, fh_or_h5):
        """
            @api {post} /express/{fh|h5}/call 发货端 - 一键呼叫
            @apiName common_express_one_key_call
            @apiGroup common_express
            @apiVersion 0.0.1

            @apiParam (body param) {int} count 运单个数
            @apiParam (body param) {json} sender 寄方信息
            @apiParam (body param) {string} sender.tel 寄方手机号
            @apiParam (body param) {string} sender.name 寄方名称
            @apiParam (body param) {string} sender.addr 寄方地址
            @apiParam (body param) {float} sender.lat 寄方地址纬度
            @apiParam (body param) {float} sender.lng 寄方地址经度

            @apiSuccessExample 成功返回示例
            HTTP/1.1 200 OK
            {express}
            @apiUse default_express

            @apiUse bad_response
        """
        try:
            kw = Schema({
                Optional("sender",
                         default={'addr': '未知地段', 'name': '收方名称', 'tel': '00000000000',
                                  'lat': 0.0, 'lng': 0.0}):
                    {
                        "addr": schema_unicode,
                        "name": schema_unicode,
                        "tel": schema_unicode,
                        Optional('lat'): schema_float,
                        Optional('lng'): schema_float,
                    },
                "count": schema_int
            }).validate(self.get_body_args())
        except SchemaError:
            self.resp_error("请将信息填写完整.")
            return

        sender = kw['sender']
        if 'lat' in sender and 'lng' in sender:
            lat_0 = sender['lat']
            lng_0 = sender['lng']
        else:
            # 解析发货人当前位置地址
            lng_0, lat_0 = yield baidumap_api.async_get_coordinates("", "", sender["addr"])
        shop = {
            'id': self.shop_info['id'],
            'name': sender['name'],
            'tel': sender['tel'],
            'm_type': fh_or_h5,

            'lat': lat_0,
            'lng': lng_0,
            'address': sender['addr'],
        }
        # 1. 执行一键呼叫
        resp_obj = yield self.async_fetch(express.redirect_one_key_call(
            shop=shop,
            count=kw['count']
        ))
        # 2. 数据组log: 一键呼叫
        if http_code.is_success(resp_obj.code):
            try:
                yield java_windlog.log_create(
                    type=21001,
                    shopId=shop["id"],
                    createTime=arrow.utcnow().isoformat(),
                    amount=kw["count"],
                    locationLat=shop["lat"],
                    locationLng=shop["lng"],
                    caseId=str(resp_obj.parse_response()[0]["id"])
                )
            except Exception as e:
                logging.warn(e.message)
        # 3. 不管收件结果如何, 原样返回
        self.resp(content=resp_obj.content, status_code=resp_obj.code)


class ExpressHandler(ShopHandler):
    @coroutine
    def get(self, fh_or_h5):
        """
            @api {get} /express/{ps|fh|h5}/multi 通用 - 运单列表和运单搜索
            @apiName common_express_query
            @apiGroup common_express
            @apiVersion 0.0.1

            @apiParam (query param) {string} [term] 模糊查询的值
            @apiParam (query param) {string} [term_keys=number] 需要模糊查询的字段, 逗号分隔
            @apiParam (query param) {string} [pkg_id] 包裹id
            @apiParam (query param) {string} [status] 大分类状态
            @apiParam (query param) {string} [sub_status] 细分类的状态
            @apiParam (query param) {string} [time_type=create_time] 需要限制的时间类型
            @apiParam (query param) {string} [start_time] 开始时间
            @apiParam (query param) {string} [end_time] 结束时间
            @apiParam (query param) {string} [assignee_id] 当前运单负责人id
            @apiParam (query param) {string} [assignee_type] 当前运单负责人类型
            @apiParam (query param) {string} [watcher_tel] 当前运单负责人电话, 模糊匹配
            @apiParam (query param) {string} [watcher_id] 经手人的id
            @apiParam (query param) {string} [watcher_type] 经手人的类型
            @apiParam (query param) {string} [watcher_tel] 经手人的电话, 模糊匹配
            @apiParam (query param) {string} [assignee_type] 当前运单负责人类型
            @apiParam (query param) {string} [assignee_type] 当前运单负责人类型
            @apiParam (query param) {string} [fence_id] 围栏id
            @apiParam (query param) {string} [fence_name] 围栏名称, 模糊匹配
            @apiParam (query param) {int} [page] 分页号
            @apiParam (query param) {int} [count] 每页的个数
            @apiParam (query param) {int} [limit] 是否分页
            @apiParam (query param) {string} [limit] 是否分页
            @apiParam (query param) {string} [includes] 需要的字段
            @apiParam (query param) {string} [excludes] 不需要的字段
            @apiParam (query param) {string} [only] 只想要的字段

            @apiParamExample {json} 请求示例
            http://api.gomrwind.com:5000/express/ps/multi
            http://api.gomrwind.com:5000/express/fh/multi
            http://api.gomrwind.com:5000/express/song/multi
            http://api.gomrwind.com:5000/express/yun/multi

            @apiSuccessExample 成功返回示例
            HTTP/1.1 200 OK
            [
                {express}, ...
            ]
            @apiUse default_express
            @apiUse bad_response
        """
        params = self.get_query_args()
        params.update({
            "creator_id": self.shop_info['id']
        })
        yield self.resp_redirect(express.redirect_query_express(**params))


class ExpressListWithCash(ShopHandler):
    @coroutine
    def get(self, fh_or_h5_or_song):
        """
        运单列表: 待配送员定价收件
        """
        # 验证APP-fh/h5输入
        try:
            params = Schema({
                Optional('page'): schema_int,
                Optional('count'): schema_int,
                Optional('only'): schema_unicode_multi
            }).validate(self.get_query_args())
        except SchemaError:
            self.resp_args_error()
            return

        # 1. 定制列表查询条件: 取待配送员定价收件的运单列表
        params.update({
            'creator__id': self.shop_info['id'],
            'status__status__in': [ExprState.STATUS_PRE_CREATED, ExprState.STATUS_CREATED],
            'only': ['status', 'number', 'fee', 'node', 'id'] if 'only' not in params else params['only'],
            'order_by': ['-status.sub_status', '-update_time']
        })
        resp_expr_list = yield self.async_fetch(express.redirect_pickle_search(params))
        result_expr_list = resp_expr_list.content
        # 2. 计算该商户总计待支付的运费
        pipeline = [
            # 取待配送员定价收件的运单列表
            {
                "$match": {
                    "creator.id": self.shop_info['id'],  # 是该商户下的单
                    "status.sub_status": ExprState.SUB_STATUS_PRE_PRICED,  # 下单后已定价,尚未成功支付
                    "fee.fh": {"$exists": True, "$ne": None}
                }
            },
            # 加一下, 获得自己总计待支付的运费
            {
                "$group": {
                    "_id": None,
                    "cash": {"$sum": "$fee.fh"},
                    "number_list": {"$addToSet": "$number"}
                }
            }
        ]
        resp_cash = yield self.async_fetch(express.redirect_aggregation(pipeline=pipeline))
        result_cash = 0 if not resp_cash.content else resp_cash.content[0]['cash']
        result_num_list = [] if not resp_cash.content else resp_cash.content[0]['number_list']

        self.set_header('X-Resource-Count', resp_expr_list.headers.get('X-Resource-Count', 0))
        # todo 如果count超过多少的话, 做cash和number_list的限制
        self.resp({'expr_list': result_expr_list, 'cash': round(result_cash, 2), 'number_list': result_num_list})

    @coroutine
    def patch(self, fh_or_h5):
        """
        商户支付单个/多个运单
        """
        self.resp_forbidden('该接口也要关闭啦, 不能给你们调用啦')
        return
        try:
            kw = Schema({
                'cash': schema_float_2,
                'number_list': [
                    schema_unicode
                ]
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e)
            self.resp_args_error()
            return

        yield self.resp_redirect(express.redirect_perform_pay(self.shop_info['id'], kw['cash'], kw['number_list']))


class AggregationStatusHandler(ShopHandler):
    @coroutine
    def get(self, fh_or_h5):
        """
        @api {GET} /express/{fh|h5}/aggregation/status 发货段 - 统计各个状态的数据
        @apiName ps_express_aggregation_status
        @apiGroup app_ps
        @apiVersion 0.0.1

        @apiParam (query param) {string} [term] 模糊查询的值
        @apiParam (query param) {string} [term_keys=number] 需要模糊查询的字段, 逗号分隔
        @apiParam (query param) {string} [pkg_id] 包裹id
        @apiParam (query param) {string} [status] 大分类状态
        @apiParam (query param) {string} [sub_status] 细分类的状态
        @apiParam (query param) {string} [time_type=create_time] 需要限制的时间类型
        @apiParam (query param) {string} [start_time] 开始时间
        @apiParam (query param) {string} [end_time] 结束时间
        @apiParam (query param) {string} [assignee_id] 当前运单负责人id
        @apiParam (query param) {string} [assignee_type] 当前运单负责人类型
        @apiParam (query param) {string} [fence_id] 围栏id
        @apiParam (query param) {string} [fence_name] 围栏名称

        @apiSuccessExample {json} 成功返回例子

        {
            # 这个分类下是总计的个数
            "status": {
                "SENDING": 2,    # 所有在配送中
                "FINISHED": 1,   # 所有完结
                "CREATED": 0     # 所有在初始状态
            },
            # 这个分类下是细分的个数
            "sub_status": {
                "SENDING": 1,    # 派件中
                "REFUSE": 0,     # 被收件人拒绝
                "CREATED": 0,    # 初始的状态
                "VALIDATING": 1, # 审核中
                "DELAY": 1,      # 延迟派件
                "WAREHOUSE": 0,  # 仓库中
                "FINISHED": 1,   # 妥投
                "VALID": 0,      # 审核通过
                "CANCEL": 0,     # 商户取消
                "TRASH": 0,      # 无法送达
                "NO_CASH": 0     # 审核不通过
            }
        }

        """
        param = self.get_query_args()

        param.update({
            "creator_id": self.shop_info['id'],
        })
        yield self.resp_redirect(express.redirect_aggregation_status(param))


class Fence(ShopHandler):
    @coroutine
    def get(self):
        """
        简单查
        """
        yield self.resp_redirect(node.redirect_get_fence(**self.get_query_args()))
