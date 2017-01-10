# coding: utf-8


import arrow
import logging

from .apis import express
from .apis import node
from mongoengine import Q
from schema import Schema, Optional, Or, SchemaError
from tools_lib import java_windlog
from tools_lib.bl_call import CallState
from tools_lib.bl_expr import ExprState
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.gtornado import http_code
from tools_lib.gtornado.escape import (schema_float_2, schema_int, schema_utf8, schema_bool, schema_unicode_multi,
                                       schema_unicode, schema_unicode_empty, schema_float, schema_objectid)
from tools_lib.gtornado.escape import schema_loc
from tools_lib.gtornado.web2 import ManHandler
from tools_lib.pricing import pricing, DEFAULT_CATEGORY, fh_base
from tornado.gen import coroutine


# == 公共呼叫池+我的呼叫列表: 任务--收件
class Call(ManHandler):
    @coroutine
    def get(self):
        try:
            qs = Schema({
                Optional(object): object,
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("only", default=[]): schema_unicode_multi,
                Optional("order_by", default=['status', '-update_time']): schema_unicode_multi,
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error()
            return
        query = {
            'Q': Q(
                __raw__={
                    '$or': [
                        # 我抢到的没结束的呼叫
                        {
                            '$and': [
                                {'status': {'$ne': CallState.STATUS_CLOSED}},  # 已经结束的呼叫不返回
                                {'assignee.id': self.man_info['id']},  # 我抢到的呼叫
                            ]
                        },
                        # 公有池的推送给我的呼叫
                        {
                            '$and': [
                                {'status': CallState.STATUS_ALL},
                                {'watchers': {'$elemMatch': {'id': self.man_info['id']}}},
                            ]
                        }
                    ]
                }
            ),
            'page': qs['page'],
            'count': qs['count'],
            'limit': qs['limit'],

            'only': qs['only'],
            'order_by': qs['order_by']
        }
        # 发货时间（年月日 时分秒）、发货客户名称、发货客户电话、发货客户地址、发货客户地址所在围栏、呼叫单数
        yield self.resp_redirect(express.redirect_query_one_key_call(query))


# == 呼叫内的客户运单列表: 任务--收件--立即前往--客户运单
class ExprListInCall(ManHandler):
    @coroutine
    def get(self):
        try:
            qs = Schema({
                'call_id': schema_objectid,
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("only", default=''): schema_unicode,
                Optional("order_by", default='-status.status,-create_time'): schema_unicode,
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error()
            return
        yield self.resp_redirect(express.redirect_query_call_expr_list(qs))


# == 抢呼叫
class AssignCallToMe(ManHandler):
    @coroutine
    def patch(self):
        """
        抢呼叫
        :param :
        :return:
        """
        try:
            kw = Schema({
                'call_id': schema_unicode,
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e)
            self.resp_args_error(e.message)
            return
        operator = self.man_info

        # 1. 执行抢呼叫
        resp_obj = yield self.async_fetch(express.redirect_perform_call_event(
            call_id=kw['call_id'],
            operation=CallState.EVENT_ASSIGN_TO_ME,
            operator=operator,
            assignee=operator
        ))

        # 2. 数据组log: 抢呼叫
        if http_code.is_success(resp_obj.code):
            try:
                call = resp_obj.content
                yield java_windlog.log_create(
                    type=21002,
                    creatorId=call["assignee"]["id"],
                    createTime=call["create_time"],
                    locationLat=call["loc"]["lat"],
                    locationLng=call["loc"]["lng"],
                    caseId=call["id"]
                )
            except Exception as e:
                logging.warn(e.message)

        # 3. 不管收件结果如何, 原样返回
        self.resp(content=resp_obj.content, status_code=resp_obj.code)


# == 加单: 选订单基础价格的文案们
class FhBase(ManHandler):
    @coroutine
    def get(self):
        """
        选订单基础价格的文案们
        :return:
        """
        cont = fh_base()
        self.resp(content=cont)


# == 加单: 先下单, 下单成功加入call的number_list
class AddExprToCall(ManHandler):
    @coroutine
    def patch(self):
        """
        加单
        :param :
        :return:
        """
        try:
            kw = Schema({
                'call_id': schema_unicode,
                'name': schema_unicode_empty,
                'tel': schema_unicode,

                'address': schema_unicode_empty,
                'lat': schema_float,
                'lng': schema_float,
                Optional('category', default=DEFAULT_CATEGORY): schema_unicode,
                'remark': schema_unicode_empty
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e)
            self.resp_args_error(e.message)
            return
        # 0. 解包出call_id
        call_id = kw.pop('call_id')
        # 1. 解析送达地址, 获取对应的围栏
        fence_n = yield node.query_fence_point_within([kw['lng'], kw['lat']], need_mans=True)
        # 1.1 没围栏, 拒绝加单
        if fence_n['id'] == 'x':
            msg = '找不到客户送达地址[%s][%s]%s 所在的送达围栏.' % (kw['name'], kw['address'], (kw['lat'], kw['lng']))
            logging.info(msg)
            self.resp_error('加单失败，送达地址超出服务范围')
            return
        # 1.2 有围栏, 但是围栏下没有人
        elif not fence_n['mans']:
            logging.info('找到客户送达地址[%s][%s]%s 所在送达围栏[%s], 但围栏内没人.' % (
                kw['name'], kw['address'], (kw['lat'], kw['lng']), fence_n['name']))
            self.resp_error('抱歉！该地址所在区域无人可供上门收件')
            return
        # 1.3 有围栏, 执行加单
        else:
            # 注意把mans去掉
            fence_n.pop('mans', None)
            kw['fence'] = fence_n
            operator = self.man_info
            resp_obj = yield self.async_fetch(express.redirect_perform_call_event(
                call_id=call_id,
                operation=CallState.EVENT_ADD,
                operator=operator,
                **kw
            ))
            # 2. 加单成功: 记数据组log
            if http_code.is_success(resp_obj.code):
                try:
                    call = resp_obj.content
                    yield java_windlog.log_create(
                        type=21003,
                        creatorId=self.man_info["id"],
                        createTime=arrow.utcnow().isoformat(),
                        locationLat=call["loc"]["lat"],
                        locationLng=call["loc"]["lng"],
                        shopId=call["shop_id"],
                        orderAddress=kw["address"],
                        orderLat=kw["lat"],
                        orderLng=kw["lng"],
                        caseId=call["id"]
                    )
                except Exception as e:
                    logging.warn(e.message)
            # 3. 不管加单结果如何, 原样返回
            self.resp(resp_obj.content, resp_obj.code)
            return


# == 发起收款: 获取微信/支付宝收款二维码
class PayUsFromCall(ManHandler):
    @coroutine
    def patch(self):
        """
        发起收款: 获取微信/支付宝收款二维码
        1. 改f_shop.flow_top_up
        2. 增加aeolus.call的transact_list[ {transact_num,cash,number_list,code_url,  trade_no} ]
        注意: 回调的部分, 要根据transact_num
            改flow_top_up,flow,flow_statistics;
            改aeolus.call.transact_list的trade_no;
            改aeolus.express对应于number_list里面的运单的状态们.
        :param :
        :return:
        """
        try:
            kw = Schema({
                'call_id': schema_unicode,
                'cash': schema_float_2,
                'number_list': [
                    schema_unicode
                ],
                "pay_type": schema_unicode,  # WXPAY/ALIPAY
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e)
            self.resp_args_error(e.message)
            return

        call_id = kw.pop('call_id')
        operator = self.man_info

        resp_obj = yield self.async_fetch(express.redirect_perform_call_event(
            call_id=call_id,
            operation=CallState.EVENT_PAY_US,
            operator=operator,
            **kw
        ))
        if resp_obj.code == 200:
            modified_call = resp_obj.content
            transact = modified_call['transact_list']
            self.resp(transact)
            return
        else:
            self.resp_error(resp_obj.content.get('message') if resp_obj.content else '第三方交易生成失败', resp_obj.code)
            return


# == 取消运单
class AssigneeCancel(ManHandler):
    @coroutine
    def patch(self, number):
        """
        取消运单
        :return:
        """
        try:
            kw = Schema({
                'call_id': schema_objectid,
                Optional('operating_loc', default={}): schema_loc
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error(e.message)
            return
        call_id = kw['call_id']
        operator = self.man_info
        operator['operating_loc'] = kw['operating_loc']

        yield self.resp_redirect(express.redirect_perform_call_event(
            call_id=call_id,
            operation=CallState.EVENT_CANCEL,
            operator=operator,
            number=number
        ))


# == 扫码收件
class AssigneeSJ(ManHandler):
    @coroutine
    def patch(self, number):
        """
        收件
        :param number:
        :return:
        """
        try:
            kw = Schema({
                'call_id': schema_objectid,
                Optional("operating_loc", default={}): schema_loc
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error(e.message)
            return
        call_id = kw['call_id']
        operator = self.man_info
        operator["operating_loc"] = kw["operating_loc"]
        # 1. 执行收件
        resp_obj = yield self.async_fetch(express.redirect_perform_call_event(
            call_id=call_id,
            operation=CallState.EVENT_SJ,
            operator=operator,
            number=number
        ))
        # 2. 数据组log: 扫码收件(客户->收件员)
        try:
            if resp_obj.code == 200:
                # 收件成功, 开始记日志
                expr_resp_obj = yield self.async_fetch(express.redirect_get_express(number, only='fee'))
                # 取运单价格, 记入日志
                if expr_resp_obj.code == 200:
                    expr_resp = expr_resp_obj.content
                    fee_fh = expr_resp['fee']['fh']
                    call = resp_obj.content
                    yield java_windlog.log_create(
                        type=21004,
                        creatorId=self.man_info["id"],
                        createTime=arrow.utcnow().isoformat(),
                        orderId=number,
                        orderSum=fee_fh,
                        caseId=call["id"]
                    )
                else:
                    logging.warn('拿不到价格, number==[{number}]'.format(number=number))
            else:
                logging.warn('收件失败, number==[{number}]'.format(number=number))
        except Exception as e:
            logging.warn(e.message)

        # 3. 不管收件结果如何, 原样返回
        self.resp(content=resp_obj.content, status_code=resp_obj.code)


# == 关闭呼叫入口
class CloseThisCall(ManHandler):
    @coroutine
    def patch(self):
        """
        关闭呼叫入口
        :param :
        :return:
        """
        try:
            kw = Schema({
                'call_id': schema_unicode,
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e)
            self.resp_args_error(e.message)
            return
        operator = self.man_info
        yield self.resp_redirect(express.redirect_perform_call_event(
            call_id=kw['call_id'],
            operation=CallState.EVENT_CLOSE,
            operator=operator
        ))


class Pricing(ManHandler):
    @coroutine
    def get(self):
        """
        @api {GET} /express/ps/single/pricing 配送系列 - 拿计价
        @apiName ps_express_single_get_price
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

    @coroutine
    def patch(self):
        """
        @api {PATCH} /express/ps/single/pricing 配送系列 - 所有角色改价
        @apiName ps_express_single_pricing
        @apiGroup app_ps

        @apiParam (body param) {string} number 运单号
        @apiParam (body param) {float} weight 运单溢价对应的重量
        """
        # 用完善运单信息的接口去支持
        try:
            kw = Schema({
                'number': schema_utf8,
                'weight': schema_float_2,
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e)
            self.resp_args_error()
            return

        operator = self.man_info
        yield self.resp_redirect(express.redirect_modify_fee(kw['number'],
                                                             {
                                                                 'weight': kw['weight'],
                                                                 'operator': operator
                                                             }))


class SingleExpressHandler(ManHandler):
    @coroutine
    def get(self, number):
        qs = self.get_query_args()
        yield self.resp_redirect(express.redirect_get_express(number, **qs))


class AggregationStatusHandler(ManHandler):
    @coroutine
    def get(self):
        """
        @api {GET} /express/ps/aggregation/status 配送端 - 数据页面
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
            "watcher_id": self.man_info['id'],
            "watcher_type": self.man_info['m_type']
        })

        yield self.resp_redirect(express.redirect_aggregation_status(param))


# == 获取抢单列表
class ExpressPool(ManHandler):
    @coroutine
    def get(self):
        """
        获取抢单列表
        :return:
        """
        try:
            qs = Schema({
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("only", default=list): schema_unicode_multi,
                Optional("order_by", default=['-update_time']): schema_unicode_multi,
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error(e.message)
            return
        qs.update({
            "candidates__id": self.man_info['id'],  # 我能看到的
            "occupant": {},  # 还没被人抢到的
        })
        yield self.resp_redirect(express.redirect_pickle_search(qs))


# == 抢单
class WillOccupy(ManHandler):
    @coroutine
    def patch(self):
        """
        抢单
        :param :
        :return:
        """
        try:
            kw = Schema({
                'number': schema_unicode,
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e)
            self.resp_args_error(e.message)
            return
        operator = self.man_info
        yield self.resp_redirect(express.redirect_perform_expr_event(
            number=kw['number'],
            operation=ExprState.EVENT_QD,
            operator=operator
        ))


# == 收派列表(任务列表)
class ExpressSending(ManHandler):
    @coroutine
    def get(self):
        """
        获取收派列表(任务列表)
        :return:
        """
        try:
            qs = Schema({
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("order_by", default=['-update_time']): schema_unicode_multi,
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error(e.message)
            return
        my_id = self.man_info['id']

        q = Q(**{'status__sub_status__in': [ExprState.SUB_STATUS_SENDING, ExprState.SUB_STATUS_DELAY,
                                            ExprState.SUB_STATUS_REFUSE]}) & (  # 只关注派件中/延迟/拒收
                Q(**{"assignee__id": my_id}) |  # 持有人是我
                Q(**{"occupant__id": my_id}))  # 占坑人是我
        qs['Q'] = q
        resp_obj = yield self.async_fetch(express.redirect_pickle_search(qs))
        if resp_obj.code == 200:
            resp = resp_obj.content
            # 只要返回 number, node_n.loc.addr, node_n.fence.name
            ret = add_tag_to_expr(resp, my_id=my_id)
            self.set_header('X-Resource-Count', resp_obj.headers.get('X-Resource-Count', 0))
            self.resp(ret)
        else:
            self.resp(resp_obj.content, resp_obj.code)
            return


# == 运单地图化: 对司机没有意义
class ExpressMap(ManHandler):
    @coroutine
    def get(self):
        """
        对收件员: 待转交 (将收到的包裹放到from的站点下)
        对派件员: 待取件 / 待妥投 (从to的站点取要我去派件[to经纬度]的包裹 / 将我手上的件派掉[to经纬度])
        司机不要打开运单地图化, 将没有参考意义.
        :return:
        """
        try:
            qs = Schema({
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error(e.message)
            return
        my_id = self.man_info['id']

        # 1. 取我所在的围栏们
        fences_obj = yield self.async_fetch(node.redirect_get_fence(man_id=my_id, only='name,points'))
        if fences_obj.code == 200:
            fences = fences_obj.content
        else:
            self.resp(fences_obj.content, fences_obj.code)
            return

        # 2. 取其他
        q = Q(**{'status__sub_status': ExprState.SUB_STATUS_SENDING}) & (  # 只关注派件中
            Q(**{"assignee__id": my_id}) |  # 持有人是我
            Q(**{"occupant__id": my_id}))  # 占坑人是我
        qs['Q'] = q
        resp_obj = yield self.async_fetch(express.redirect_pickle_search(qs))
        if resp_obj.code == 200:
            resp = resp_obj.content
            _stop = set()
            # 只要返回 要将收到的包裹放过去的站点们; 要去拿包裹的站点们、要去拿的包裹送达经纬度、我手上的包裹的送达经纬度
            ret = {
                'stop': [],  # 要将收到的包裹放过去的站点们 (我的待转交) + 要去拿包裹的站点们 (我的待取件)
                'qj': [],  # 要去拿的包裹送达经纬度
                'tt': [],  # 我手上的包裹的送达经纬度
                # 'fence': []  # 我所在的一亩三分地(围栏)
            }
            for expr in resp:
                assignee = expr['assignee']
                occupant = expr['occupant']
                # == 子状态是SENDING, 计算 待转交(A,S)/待取件(S,B)/待妥投(B)
                # 持有人是我, 并且需要转交(A,S)
                if assignee.get('id') == my_id and assignee['need_zj'] == True:
                    # 待转交
                    zj_stop = expr['node']['node_0']['fence']['node']
                    if zj_stop['id'] not in _stop:
                        ret['stop'].append(zj_stop)
                        _stop.add(zj_stop['id'])
                # 持有人是我, 不需要转交(我是最后一棒)(B)
                elif assignee.get('id') == my_id and assignee['need_zj'] == False:
                    # 待妥投
                    to = expr['node']['node_n']
                    point = {
                        'number': expr['number'],
                        'name': to['name'],
                        'tel': to['tel'],
                        'addr': to['addr'],
                        'lat': to['lat'],
                        'lng': to['lng'],
                    }
                    ret['tt'].append(point)
                # 占坑人是我(S,B)
                elif occupant.get('id') == my_id:
                    # 待取件
                    to = expr['node']['node_n']
                    point = {
                        'number': expr['number'],
                        'name': to['name'],
                        'tel': to['tel'],
                        'addr': to['addr'],
                        'lat': to['lat'],
                        'lng': to['lng'],
                    }
                    ret['qj'].append(point)
                    qj_stop = expr['node']['node_n']['fence']['node']
                    if qj_stop['id'] not in _stop:
                        ret['stop'].append(qj_stop)
                        _stop.add(qj_stop['id'])

            self.set_header('X-Resource-Count', resp_obj.headers.get('X-Resource-Count', 0))
            # 合并结果
            ret['fence'] = fences
            self.resp(ret)
            return
        else:
            self.resp(resp_obj.content, resp_obj.code)
            return


# == 通用查询: 默认查询assignee/occupant是我的单
class ExpressHandler(ManHandler):
    @coroutine
    def get(self):
        try:
            qs = Schema({
                Optional('sub_status'): schema_unicode,  # 状态筛选
                Optional('status'): schema_unicode,  # 查看历史任务

                Optional('term'): schema_unicode,  # 用于搜索
                Optional('term_keys'): schema_unicode,

                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("order_by", default='-update_time'): schema_unicode,
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error(e.message)
            return
        my_id = self.man_info['id']
        qs.update({
            "assignee_id": my_id,  # 会|occupant__id
            # "assignee_type": self.man_info['m_type'],
        })
        resp_obj = yield self.async_fetch(express.redirect_query_express(**qs))
        if resp_obj.code == 200:
            resp = resp_obj.content
            ret = add_tag_to_expr(resp, my_id=my_id)
            self.set_header('X-Resource-Count', resp_obj.headers.get('X-Resource-Count', 0))
            self.resp(ret)
            return
        else:
            self.resp(resp_obj.content, resp_obj.code)
            return


# == 交接人列表
class Candidates(ManHandler):
    @coroutine
    def get(self):
        """
        获取交接人列表
        :return:
        """
        try:
            qs = Schema({
                'number': schema_unicode,
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error(e.message)
            return
        # todo 交接人数量过多, 用bl接口处理array slicing
        yield self.resp_redirect(express.redirect_get_express(qs['number'], **{'only': 'candidates'}))


class AssigneeQJ(ManHandler):
    @coroutine
    def patch(self, number):
        """
        @api {PATCH} /express/ps/single/{number}/assignee_qj 配送端 - 扫码取件
        @apiName ps_express_single_assignee_qj
        @apiGroup app_ps

        @apiParam (url param) {string} number 运单号

        @apiParam (body param) {object} operating_loc 操作地理信息
        @apiParam (body param) {float} operating_loc.lat 经度
        @apiParam (body param) {float} operating_loc.lng 纬度
        @apiParam (body param) {string} operating_loc.addr 地址信息


        @apiParamExample {json} 请求示例
        patch http://api.gomrwind.com:5000/express/ps/single/000001000333/assignee_qj
        {}
        @apiUse bad_response
        """
        try:
            data = Schema({
                Optional("operating_loc", default={}): schema_loc  # 操作当时的地理位置信息
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.error(e.message)
            self.resp_args_error()
            return
        operator = self.man_info
        operator["operating_loc"] = data["operating_loc"]

        # 1. 执行扫码取件
        resp_obj = yield self.async_fetch(express.redirect_perform_expr_event(
            number=number,
            operation=ExprState.EVENT_QJ,
            operator=operator
        ))

        # 2. 数据组log: 扫码取件(人->人)
        if http_code.is_success(resp_obj.code):
            try:
                yield java_windlog.log_create(
                    type=21005,
                    creatorId=self.man_info["id"],
                    createTime=arrow.utcnow().isoformat(),
                    orderId=number
                )
            except Exception as e:
                logging.warn(e.message)

        # 3. 不管收件结果如何, 原样返回
        self.resp(content=resp_obj.content, status_code=resp_obj.code)


# == [GET] 根据id获取人员签到列表
class MySchedule(ManHandler):
    @coroutine
    def get(self):
        yield self.resp_redirect(express.redirect_get_my_schedule(self.man_info['id']))


# == [GET] 传递端搜索商户的发货地址、收货地址
class CliAddressFuzzySearch(ManHandler):
    @coroutine
    def get(self):
        """
        @api {GET} /express/ps/client_address/fuzzy_search 模糊搜索商户地址信息(发货收货)
        @apiName ps_express_fuzzy_search_shop_client_address
        @apiGroup app_ps
        @apiVersion 0.0.1

        @apiParam (query string) {string} term 关键字
        @apiParam (query string) {string} call_id 呼叫id

        @apiSuccessExample {json} 成功返回
        HTTP/1.1 200 OK
        [
            {
                "lat": 30.2592444615,
                "lng": 120.2193754157,
                "tel": "18898880988",
                "name": "sdfdsf",
                "addr": "测试前端"
            }, ...
        ]
        """
        try:
            data = Schema({
                "term": schema_utf8,
                "call_id": schema_utf8
            }).validate(self.get_query_args())
        except:
            self.resp_error("输入错误.")
            return
        yield self.resp_redirect(express.redirect_search_client_address(
            term=data["term"],
            search_in=["node_n"],
            call_id=data["call_id"]
        ))


# == 给(派件中)运单加上状态标签
def add_tag_to_expr(expr_list, my_id):
    # 只要返回 number, node_n.loc.addr, node_n.fence.name
    ret = []
    for expr in expr_list:
        assignee = expr['assignee']
        occupant = expr['occupant']
        item = {
            'number': expr['number'],
            'node': {
                'node_n': {
                    'loc': {
                        'addr': expr['node']['node_n']['addr']
                    },
                    'fence': {
                        'name': expr['node']['node_n']['fence']['name']
                    }
                }
            }
        }
        # == 子状态不是SENDING, tag是状态的中文名: 包括延迟派件在内
        sub_status = expr['status']['sub_status']
        if sub_status != ExprState.SUB_STATUS_SENDING:
            item['tag'] = ExprState.STATUS_NAME_MAPPING[sub_status]
        # == 子状态是SENDING, 计算 待转交(A,S)/待取件(S,B)/待妥投(B)
        # 占坑人是我(S,B)
        elif occupant.get('id') == my_id:
            item['tag'] = '待取件'
        # 持有人是我, 不需要转交(我是最后一棒)(B)
        elif assignee.get('id') == my_id and assignee['need_zj'] == False:
            item['tag'] = '待派件'
        # 持有人是我, 并且需要转交(A,S)
        elif assignee.get('id') == my_id and assignee['need_zj'] == True:
            item['tag'] = '待转交'
        ret.append(item)
    return ret


class Fence(ManHandler):
    @coroutine
    def get(self):
        """
        简单查
        """
        yield self.resp_redirect(node.redirect_get_fence(**self.get_query_args()))


class FencePointWithin(ManHandler):
    @coroutine
    def get(self):
        """
        判断点是否落入任何一个围栏(外加一些逻辑条件)
        """
        resp_obj = yield self.async_fetch(node.redirect_get_fence(**self.get_query_args()))
        if not http_code.is_success(resp_obj.code):
            logging.error("fence query with error status code, message: {content}, code: {code}".format(
                content=repr(resp_obj.content),
                code=resp_obj.code
            ))
            self.resp(*resp_obj.parse_response())
            return
        if resp_obj.content==[]:
            # 不在任何围栏内
            self.resp({
                "within": False,
                "message": "该地址不在配送范围内"
            })
            return
        for f in resp_obj.content:
            if f.get("mans", []):
                # 在任一个有人的围栏内即
                self.resp({
                    "within": True,
                    "has_man": True
                })
                return
        self.resp({
            "within": True,
            "has_man": False,
            "message": "该地址不在配送范围内"
        })
