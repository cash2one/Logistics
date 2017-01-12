# coding:utf-8
"""
给yun.123feng.com用的接口.
"""


import arrow
from .apis import bl_data
from .apis.express import *
from .apis.node import *
from schema import Schema, SchemaError, Optional
from tools_lib.bl_expr import ExprState
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.gtornado.apis import multi_shop_balance
from tools_lib.gtornado.escape import (schema_unicode_empty, schema_unicode_upper, schema_date, schema_datetime,
                                       schema_unicode, schema_int, schema_bool, schema_unicode_multi, schema_float,
                                       schema_objectid, schema_hhmm)
from tools_lib.gtornado.web2 import StaffHandler
from tornado import gen


class StatCustomerPlacingOrder(StaffHandler):
    # 商户下单数据
    @gen.coroutine
    def get(self):
        # 商户名,商户注册电话,余额,当日消费,当日10:00前下单,当日10:00~14:00下单,当日14:00之后下单,当日待取件,总计待妥投
        try:
            data = Schema({
                "date": schema_date,
            }).validate(self.get_query_args())
            date = data['date']
        except SchemaError:
            self.resp_error('参数[date]解析失败')
            return
        middle = {}
        # 1. 商户名,商户注册电话,当日消费,当日10:00前下单,当日10:00~14:00下单,当日14:00之后下单
        start_time, end_time = TimeZone.day_range(value=date)
        pipeline = [
            # 取今天的所有有效运单
            {
                "$match": {
                    "create_time": {
                        "$gt": start_time,
                        "$lt": end_time
                    },
                    "status.sub_status": {"$ne": ExprState.SUB_STATUS_CANCEL}
                }
            },
            # 按照[商户,小时]分组
            {
                "$group": {
                    "_id": {
                        "creator_id": "$creator.id",
                        "hour": {"$hour": {"$add": ['$create_time', 28800000]}},
                    },
                    "tel": {"$first": "$creator.tel"},
                    "name": {"$first": "$creator.name"},
                    "expr_count": {"$sum": 1},
                    # 暂时除了pre_created的运单才算是消费了
                    "expense": {"$sum": {"$cond": [{"$ne": ["$status.status", "PRE_CREATED"]}, "$fee.fh", 0]}}
                }
            },
            # 根据[商户,小时]分组计算10:00前,10:00~14:00,14:00后下单数量
            {
                "$group": {
                    "_id": {
                        "creator_id": "$_id.creator_id",
                    },
                    "tel": {"$first": "$tel"},
                    "name": {"$first": "$name"},
                    "expense": {"$sum": "$expense"},
                    "count_before_10am": {"$sum": {"$cond": [{"$lt": ["$_id.hour", 10]}, "$expr_count", 0]}},
                    "count_10am_to_2pm": {"$sum": {
                        "$cond": [{"$and": [{"$gte": ["$_id.hour", 10]}, {"$lt": ["$_id.hour", 14]}]}, "$expr_count",
                                  0]}},
                    "count_after_2pm": {"$sum": {"$cond": [{"$gte": ["$_id.hour", 14]}, "$expr_count", 0]}},
                    "count_all": {"$sum": "$expr_count"}
                }
            },
            {
                "$sort": {
                    "count_all": -1,
                }
            }
        ]
        result = yield self.async_fetch(redirect_aggregation(pipeline=pipeline))
        content = result.content
        # 从这里拿到所有的商户id
        creator_ids = []
        for c in content:
            creator_id = c['_id']['creator_id']
            tel = c['tel']
            name = c['name']
            expense = c['expense']
            # 10点之前下单数量
            count0 = c['count_before_10am']
            # 10-14点下单数量
            count1 = c['count_10am_to_2pm']
            # 14点之后下单数量
            count2 = c['count_after_2pm']
            # 当日总计下单量
            _count_all = c['count_all']
            # print("[%s] %s+%s+%s=%s 消費:%s" % (name, count0, count1, count2, _count_all, expense))
            creator_ids.append(creator_id)
            middle[creator_id] = dict(name=name, tel=tel, expense=expense, count_before_10am=count0,
                                      count_10am_to_2pm=count1, count_after_2pm=count2, count_all=_count_all)

        # 2. 当日待取件, 当日待妥投
        pipeline = [
            # 取今天在<creator_ids>里面的所有运单
            {
                "$match": {
                    "create_time": {
                        "$gt": start_time,
                        "$lt": end_time
                    },
                    "creator.id": {
                        "$in": creator_ids
                    }
                }
            },
            # 按照[商户,状态条件]分组
            {
                "$group": {
                    "_id": {
                        "creator_id": "$creator.id",
                    },
                    "count_created": {"$sum": {"$cond": [{"$eq": ["$status.status", "PRE_CREATED"]}, 1, 0]}},
                    "count_sending": {"$sum": {"$cond": [{"$eq": ["$status.status", "SENDING"]}, 1, 0]}},
                    "count_all": {"$sum": 1}
                }
            },
            {
                "$sort": {
                    "count_all": -1,
                }
            }
        ]
        result = yield self.async_fetch(redirect_aggregation(pipeline=pipeline))
        for c in result.content:
            creator_id = c['_id']['creator_id']
            # 待取貨
            count0 = c['count_created']
            # 派件中
            count1 = c['count_sending']
            # 当日总计下单量
            _count_all = c['count_all']
            # print("[%s] 待取貨:%s 派件中:%s 總計:%s" % (name, count0, count1, _count_all))
            middle[creator_id]['count_created'] = count0
            middle[creator_id]['count_sending'] = count1

        # 3. 拿余额
        balances = yield multi_shop_balance(creator_ids)

        # 4. 拼结果
        fin = []
        for cid in creator_ids:
            middle[cid]['id'] = cid
            middle[cid]['balance'] = balances[cid]
            fin.append(middle[cid])
        self.resp(fin)


# == 站点 ==
class OneNode(StaffHandler):
    @gen.coroutine
    def get(self):
        """
        站点列表
        :return:
        """
        try:
            qs = Schema({
                "id": schema_objectid,
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        raw_query = {'id': qs['id']}
        ret = yield self.async_fetch(redirect_node_simple_query(raw_query, **qs))
        if ret.code == 200:
            nodes = ret.content
            if nodes:
                node = nodes[0]
                tt = node['time_table']
                tm_dict = {}
                for tm in tt:
                    t, man = tm['t'], tm.get('man')
                    if t in tm_dict:
                        tm_dict[t].append(man)
                    else:
                        tm_dict[t] = [man] if man else []
                new_tt = [{'t': k, 'mans': tm_dict[k]} for k in sorted(tm_dict.keys())]
                node['time_table'] = new_tt
                self.resp(node)
            else:
                self.resp_not_found('找不到对应的站点: %s' % qs['id'])
        else:
            self.resp_error(ret.content, ret.code)


class Node(StaffHandler):
    @gen.coroutine
    def get(self):
        """
        站点列表
        :return:
        """
        try:
            qs = Schema({
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("only"): schema_unicode,
                Optional("order_by", default='name'): schema_unicode,
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        raw_query = {}
        yield self.resp_redirect(redirect_node_simple_query(raw_query, **qs))

    @gen.coroutine
    def post(self):
        """
        站点添加
        :return:
        """
        try:
            kw = Schema({
                'name': schema_unicode,
                'loc': {
                    'lat': schema_float,
                    'lng': schema_float,
                    'address': schema_unicode,
                }
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        yield self.resp_redirect(redirect_create_node(kw['name'], kw['loc']))

    @gen.coroutine
    def delete(self):
        """
        站点删除
        :return:
        """
        try:
            kw = Schema({
                'id': schema_unicode
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        resp_obj = yield self.async_fetch(redirect_delete_node(kw['id']))

        # 尝试删除该站点下所有围栏内记录的该站点信息
        query = {'node__id': kw['id']}
        self.async_fetch(redirect_delete_fence(query))

        if resp_obj.code == 200:
            self.resp(resp_obj.content)
        else:
            self.resp_error(resp_obj.content, resp_obj.code)


class NodeModifyBasic(StaffHandler):
    @gen.coroutine
    def patch(self):
        """
        站点名,地址修改
        :return:
        """
        try:
            kw = Schema({
                'id': schema_objectid,
                Optional('name'): schema_unicode,
                Optional('loc'): {
                    'lat': schema_float,
                    'lng': schema_float,
                    'address': schema_unicode,
                },
            }).validate(self.get_body_args())
            node_id = kw.pop('id')
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error('参数解析失败: %s' % e.message)
            return
        # == 站点名, 地址修改
        if 'loc' in kw:
            point = {
                "type": "Point",
                "coordinates": [kw['loc']['lng'], kw['loc']['lat']]
            }
            kw['point'] = point
        resp_obj = yield self.async_fetch(redirect_modify_node(query={'id': node_id}, **kw))
        if resp_obj.code == 200:
            # == 同时去修改围栏里面记录的站点信息
            update = {}
            if 'name' in kw:
                update['node__name'] = kw['name']
            if 'loc' in kw:
                update['node__loc'] = kw['loc']
            self.async_fetch(redirect_patch_fence(query={'node__id': node_id}, **update))
        else:
            self.resp_error(resp_obj.content, resp_obj.code)


class NodeAddTime(StaffHandler):
    @gen.coroutine
    def patch(self):
        """
        添加时刻(与人)
        :return:
        """
        try:
            kw = Schema({
                'id': schema_objectid,
                't': schema_hhmm,  # HH:mm
                Optional('mans'): [
                    {
                        'id': schema_objectid,
                        'name': schema_unicode,
                        'tel': schema_unicode,
                        Optional('m_type', default='man'): schema_unicode,
                        'client_id': schema_unicode
                    }
                ],
            }).validate(self.get_body_args())
            node_id = kw.pop('id')
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error('参数解析失败: %s' % e.message)
            return
        # == 时刻已经存在:
        resp_obj = yield self.async_fetch(redirect_node_simple_query({'id': node_id, 'time_table__t': kw['t']}))
        if resp_obj.code == 200 and resp_obj.content and len(resp_obj.content) == 1:
            self.resp_error('时间已存在, 请去编辑页面修改')
            return
        # == 添加时刻与人: 去除重复的人
        if 'mans' in kw:
            man_ids = set([man['id'] for man in kw['mans']])
            if len(man_ids) != len(kw['mans']):
                msg = '添加时刻下的人员有重复'
                logging.warn(msg)
                self.resp_error(msg)
                return
            else:
                tm_list = [{'t': kw['t'], 'man': man} for man in kw['mans']]
        # == 只添加时刻
        else:
            tm_list = [{'t': kw['t']}]

        # == 操作添加和重新排序
        update1 = {
            'add_to_set__time_table': {
                '$each': tm_list
            }
        }
        update2 = {
            'push__time_table': {
                '$each': [],
                '$sort': {'t': 1}
            }
        }
        ret = yield self.async_fetch(redirect_modify_node(query={'id': node_id}, **update1))
        if ret.code == 200:
            yield self.resp_redirect(redirect_modify_node(query={'id': node_id}, **update2))
        else:
            self.resp_error(ret.content, ret.code)


class NodeDelTime(StaffHandler):
    @gen.coroutine
    def patch(self):
        """
        删除时刻
        :return:
        """
        try:
            kw = Schema({
                'id': schema_objectid,
                't': schema_hhmm,  # HH:mm
            }).validate(self.get_body_args())
            node_id = kw.pop('id')
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error('参数解析失败: %s' % e.message)
            return
        # == 删除时刻
        update = {
            'pull__time_table': {
                't': kw['t'],
                # '$sort': {'t': 1}
            }
        }
        yield self.resp_redirect(redirect_modify_node(query={'id': node_id}, **update))


class NodeModifyMan(StaffHandler):
    @gen.coroutine
    def patch(self):
        """
        修改时刻下的人
        :return:
        """
        try:
            kw = Schema({
                'id': schema_objectid,
                't': schema_hhmm,  # HH:mm
                Optional('new_t'): schema_hhmm,  # HH:mm
                Optional('mans'): [
                    {
                        'id': schema_objectid,
                        'name': schema_unicode,
                        'tel': schema_unicode,
                        Optional('m_type', default='man'): schema_unicode,
                        'client_id': schema_unicode
                    }
                ],
            }).validate(self.get_body_args())
            node_id = kw.pop('id')
            old_t = kw['t']
            new_t = old_t
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error('参数解析失败: %s' % e.message)
            return
        # == 如果时刻值要改
        if 'new_t' in kw:
            new_t = kw['new_t']
        # == 要添加时刻与人: 去除重复的人
        if 'mans' in kw:
            man_ids = set([man['id'] for man in kw['mans']])
            if len(man_ids) != len(kw['mans']):
                msg = '添加时刻下的人员有重复'
                logging.warn(msg)
                self.resp_error(msg)
                return
            else:
                tm_list = [{'t': new_t, 'man': man} for man in kw['mans']]
        # == 只剩下时刻
        else:
            tm_list = [{'t': new_t}]

        # == 操作和重新排序
        update1 = {
            'pull__time_table': {'t': old_t},  # 先删除
        }
        del_result = yield self.async_fetch(redirect_modify_node(query={'id': node_id}, **update1))
        if del_result.code == 200:
            update2 = {
                'add_to_set__time_table': {  # 再添加
                    '$each': tm_list
                }
            }
            add_result = yield self.async_fetch(redirect_modify_node(query={'id': node_id}, **update2))
            if add_result.code == 200:
                update3 = {  # 最后排序
                    'push__time_table': {
                        '$each': [],
                        '$sort': {'t': 1}
                    }
                }
                yield self.resp_redirect(redirect_modify_node(query={'id': node_id}, **update3))
        else:
            self.resp_error(content=del_result.content, status_code=del_result.code)
            return


class Call(StaffHandler):
    @gen.coroutine
    def get(self):
        end = arrow.utcnow()
        start = end.replace(days=-3)

        qs = Schema({
            Optional(object): object,
            Optional('start', default=start.datetime): schema_datetime,
            Optional('end', default=end.datetime): schema_datetime,
            Optional("page", default=1): schema_int,
            Optional("count", default=20): schema_int,
            Optional("limit", default=1): schema_bool,

            Optional("only", default=[]): schema_unicode_multi,
            Optional("order_by", default=['-create_time']): schema_unicode_multi,
        }).validate(self.get_query_args())
        query = {
            'create_time__gte': qs['start'],
            'create_time__lt': qs['end'],

            'page': qs['page'],
            'count': qs['count'],
            'limit': qs['limit'],

            'only': qs['only'],
            'order_by': qs['order_by']
        }
        # 发货时间（年月日 时分秒）、发货客户名称、发货客户电话、发货客户地址、发货客户地址所在围栏、呼叫单数
        yield self.resp_redirect(redirect_query_one_key_call(query))


class Express(StaffHandler):
    @gen.coroutine
    def get(self):
        # 丢给BL处理
        qs = self.get_query_args()
        yield self.resp_redirect(redirect_query_express(**qs))


class SingleExpress(StaffHandler):
    # todo 验证token
    # [后台] 拿一个运单的详情
    @gen.coroutine
    def get(self, number):
        # 丢给BL处理
        qs = self.get_query_args()
        qs['excludes'] = 'watchers,assignee,times,id'
        yield self.resp_redirect(redirect_get_express(number=number, **qs))

    # [后台] 操作运单: 审核不通过
    @gen.coroutine
    def patch(self, number):
        """
        请求示例
        {
            "operation": "EVENT_NO_CASH",
            "operator":{
                "tel": "13245678901",
                "name": "测试虾饼"
            },
            "msg": "客户投诉"
        }
        """
        try:
            kw = Schema({
                "operation": schema_unicode_upper,
                "operator": {
                    "tel": schema_unicode_empty,
                    "name": schema_unicode_empty,
                    Optional(object): object
                },
                Optional("msg", default=""): schema_unicode_empty,
                Optional(object): object
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.exception(e)
            self.resp_error("参数解析失败.")
            return
        except Exception as e:
            logging.exception(e)
            self.resp_error("参数解析失败.")
            return

        if kw["operation"] not in ExprState.INSIDE_EVENTS:
            logging.warn("尚未支持[%s]操作." % kw['operation'])
            self.resp_forbidden("执行操作时被拒绝.")
            return
        # 取出app-name作为operator.m_type, 其实yun.123feng是没有app-name的
        kw['operator']['m_type'] = 'yun'
        kw['operator']['id'] = 'x'
        yield self.resp_redirect(redirect_perform_expr_event(number, OPERATOR_TYPE_INSIDE, **kw))


# == 围栏 ==
class Fence(StaffHandler):
    @gen.coroutine
    def get(self):
        """
        简单查
        """
        yield self.resp_redirect(redirect_get_fence(**self.get_query_args()))

    @gen.coroutine
    def post(self):
        """
        创建
        """
        yield self.resp_redirect(redirect_post_fence(self.get_body_args()))

    @gen.coroutine
    def patch(self):
        """
        修改
        """
        try:
            data = Schema({
                "id": schema_unicode,
                Optional(object): object
            }).validate(self.get_body_args())

            fence_id = data.pop("id")
        except SchemaError as e:
            self.resp_args_error(e.message)
            return
        yield self.resp_redirect(redirect_patch_fence(query={"id": fence_id}, **data))

    @gen.coroutine
    def delete(self):
        """
        删除
        """
        yield self.resp_redirect(redirect_delete_fence(query=self.get_query_args()))


# ==> 指派 派件员/司机 配送某一单
class AssigneeZP(StaffHandler):
    @gen.coroutine
    def patch(self, number):
        """
        指派
        :param number:
        :return:
        """
        try:
            kw = Schema({
                'id': schema_unicode,
                'name': schema_unicode_empty,
                'tel': schema_unicode,
                'm_type': schema_unicode_empty
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.exception(e.message)
            self.resp_args_error(e.message)
            return

        # 用来标记是内部操作的取件派送
        kw['remark'] = '后台人员指派'
        yield self.resp_redirect(redirect_perform_expr_event(
            number=number,
            operator_type=OPERATOR_TYPE_INSIDE,
            operation=ExprState.EVENT_ZP,
            operator=kw,  # 被指派人员作为assignee和watcher
        ))


class OpDataHandler(StaffHandler):
    @gen.coroutine
    def get(self):
        """
            @api {get} /express/yun/op_data 风云 - 运营数据
            @apiName yun_op_data
            @apiGroup app_fe
            @apiVersion 0.0.1

            @apiParam (query param) {string} date 一个月中的某一天

            @apiSuccessExample 成功返回示例
            HTTP/1.1 200 OK
            [
                {
                "hr_break": 0,
                "zj_pay": 0,
                "create_time": "2016-05-19T17:00:00Z",
                "cl_shift": 0,
                "dd_error_count": 1,
                "sh_valid": 0,
                "hr_invite": 0,
                "sh_register": 0,
                "sh_order": 0,
                "zj_cash_back": 0,
                "dd_count": 0,
                "hr_interview": 0,
                "zj_top_up": 0,
                "sh_complain": 0,
                "hr_consulting": 0,
                "hr_entry": 0,
                "hr_active": 0,
                "dd_tt_count": 0,
                "hr_leave": 0,
                "cl_late": 0,
                "dd_sj_count": 0,
                "hr_on_job": 2,
                "cl_depart": 0,
                "sh_visit": 0
                },
                ...
            ]
            @apiUse bad_response
        """
        try:
            data = Schema({
                "date": schema_date
            }).validate(self.get_query_args())
        except:
            self.resp_args_error()
            return

        start, end = TimeZone.month_range(value=data['date'])

        query = {
            "create_time__gte": start,
            "create_time__lte": end,
            "excludes": ["id"]
        }

        resp = yield self.async_fetch(bl_data.redirect_op_data_search(query))

        content = resp.content

        total = dict()
        for _ in content:
            for (k, v) in list(_.items()):
                if k in total:
                    total[k] += v
                else:
                    total[k] = v

        total['create_time'] = "总计"
        content.insert(0, total)
        self.resp(content=content)
