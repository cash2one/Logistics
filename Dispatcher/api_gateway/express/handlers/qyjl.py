# # coding: utf-8
# import json
# import logging
#
# from apis import express
# from mongoengine import Q
# from schema import Schema, Optional, And
# from tools_lib.bl_expr import ExprState
# from tools_lib.common_util.archived.gtz import TimeZone
# from tools_lib.gtornado.apis import get_bind_man
# from tools_lib.gtornado.escape import schema_utf8, schema_date, schema_datetime, schema_int, schema_bool, \
#     schema_utf8_multi
# from tools_lib.gtornado.web2 import ManHandler
# from tornado import gen
#
#
# def _dump(obj):
#     if hasattr(obj, 'isoformat'):
#         return obj.isoformat()
#     elif hasattr(obj, '__call__'):
#         return None
#     raise TypeError('%s is not JSON serializable' % obj)
#
#
# class QueryBuilder(object):
#     @classmethod
#     def sj(cls, man_id, m_type, start_time, end_time):
#         # 总计收件: 收件员为他, 并且符合时间的要求
#         return {
#             "watchers__0__id": man_id,
#             "watchers__0__m_type": m_type,
#             "times__sj_time__gte": start_time,
#             "times__sj_time__lte": end_time,
#         }
#
#     @classmethod
#     def not_zj(cls, man_id, m_type, start_time, end_time):
#         # 收件未转交, 收件员为他, 并且符合时间的要求, 而且没有转交时间
#         return {
#             "watchers__0__id": man_id,
#             "watchers__0__m_type": m_type,
#             "times__sj_time__gte": start_time,
#             "times__sj_time__lte": end_time,
#             "times__zj_time__exists": False,
#         }
#
#     @classmethod
#     def sending(cls, man_id, m_type, start_time, end_time):
#         # 派件中: 目前运单在他手上, 并且大状态为派件中, 且时间符合要求, 而且一定发生过转交
#         return {
#             "assignee__id": man_id,
#             "assignee__m_type": m_type,
#             "status__status": ExprState.STATUS_SENDING,
#             "times__parttime_qj_time__gte": start_time,
#             "times__parttime_qj_time__lte": end_time,
#             "times__zj_time__exists": True,
#         }
#
#     @classmethod
#     def finished(cls, man_id, m_type, start_time, end_time):
#         # 总计妥投: 目前运单在他手上, 并且子状态为妥投, 且时间符合要求
#         return {
#             "assignee__id": man_id,
#             "assignee__m_type": m_type,
#             "status__sub_status": ExprState.SUB_STATUS_FINISHED,
#             "times__parttime_tt_time__gte": start_time,
#             "times__parttime_tt_time__lte": end_time,
#         }
#
#     @classmethod
#     def error(cls, man_id, m_type, start_time, end_time):
#         return {
#             "assignee__id": man_id,
#             "assignee__m_type": m_type,
#             "status__sub_status__in": [ExprState.SUB_STATUS_DELAY, ExprState.SUB_STATUS_REFUSE,
#                                        ExprState.SUB_STATUS_TRASH],
#             "times__parttime_qj_time__gte": start_time,
#         }
#
#
# class DataHandler(ManHandler):
#     @gen.coroutine
#     def get(self):
#         """
#         @api {get} /express/qyjl/data 风云app - 数据
#         @apiVersion 0.0.1
#         @apiName qyjl_data
#         @apiGroup app_qyjl
#
#         @apiParam (query param) {string} start_time 开始时间
#         @apiParam (query param) {string} end_time 结束时间
#
#         @apiSuccessExample 成功返回示例
#             HTTP/1.1 200 OK
#             body:
#             {
#                 "sending": 2,
#                 "not_transfer": 13,
#                 "sj_delay": 13,
#                 "finished": 31,
#                 "error": 7,
#                 "sj_total": 36,
#                 "pj_delay": 2
#             }
#         """
#         try:
#             data = Schema({
#                 "start_time": schema_datetime,
#                 "end_time": schema_datetime,
#             }).validate(self.get_query_args())
#         except Exception:
#             self.resp_args_error()
#             return
#
#         # FIXME
#
#         man_list = yield get_bind_man(self.man_info['id'])
#         end_time = data['end_time']
#         day_start, _ = TimeZone.day_range(value=TimeZone.local_now())
#         m_type = "parttime"
#         # 总计收件, 待转交, 派件中, 总计妥投, 异常, 收件滞留, 派件滞留
#         query_list = [Q()] * 7
#         for man in man_list:
#             man_id = man['man_id']
#             bind_time = TimeZone.str_to_datetime(man['bind_time'])
#             if bind_time < end_time:
#                 start_time = bind_time if bind_time > data['start_time'] else data['start_time']
#                 # 总计收件: 收件员为他, 并且符合时间的要求
#                 query_list[0] |= Q(**QueryBuilder.sj(man_id, m_type, start_time, end_time))
#                 # 收件未转交, 收件员为他, 并且符合时间的要求, 而且没有转交时间
#                 query_list[1] |= Q(**QueryBuilder.not_zj(man_id, m_type, start_time, end_time))
#                 # 派件中: 目前运单在他手上, 并且子状态为派件中, 且时间符合要求, 而且一定发生过转交
#                 query_list[2] |= Q(**QueryBuilder.sending(man_id, m_type, start_time, end_time))
#                 # 总计妥投: 目前运单在他手上, 并且子状态为妥投, 且时间符合要求
#                 query_list[3] |= Q(**QueryBuilder.finished(man_id, m_type, start_time, end_time))
#
#             # 异常: 目前运单在他手上, 并且子状态在三个异常状态中, 并且在绑定时间之后发生的取件
#             query_list[4] |= Q(**QueryBuilder.error(man_id, m_type, bind_time, None))
#
#             if bind_time < day_start:
#                 # 收件滞留: 收件员为他, 收件时间在绑定之后, 今天之前, 并且还未发生转交
#                 query_list[5] |= Q(**QueryBuilder.not_zj(man_id, m_type, bind_time, day_start))
#                 # 派件滞留: 运单在他手上, 子状态还是派件中, 派件时间在绑定之后, 今天之前
#                 query_list[6] |= Q(**QueryBuilder.sending(man_id, m_type, bind_time, day_start))
#
#         @gen.coroutine
#         def get_count(q):
#             count = 0
#             if not q.empty:
#                 query = {
#                     "Q": q,
#                     "count": 0,
#                 }
#                 resp = yield self.async_fetch(express.redirect_pickle_search(query))
#                 count = resp.headers.get('X-Resource-Count', 0)
#             raise gen.Return(count)
#
#         req_list = [get_count(q) for q in query_list]
#         count = yield req_list
#
#         content = {
#             "sj_total": count.pop(0),
#             "not_transfer": count.pop(0),
#             "sending": count.pop(0),
#             "finished": count.pop(0),
#             "error": count.pop(0),
#             "sj_delay": count.pop(0),
#             "pj_delay": count.pop(0),
#         }
#
#         self.resp(content=content)
#
#
# class DataExplainHandler(ManHandler):
#     @gen.coroutine
#     def get(self):
#         """
#         @api {get} /express/qyjl/data/explain 风云app - 数据说明
#         @apiVersion 0.0.1
#         @apiName qyjl_data_explain
#         @apiGroup app_qyjl
#
#
#         @apiSuccessExample 成功返回示例
#             HTTP/1.1 200 OK
#             body:
#             [
#                 {
#                     "title": "总计收件？",
#                     "description": "从客户处收取的件。",
#                 },
#                 ...
#             ]
#
#         """
#         content = [
#             {
#                 "title": "收件待转交？",
#                 "description": "从客户处收的, 但未转交出去的件",
#             },
#             {
#                 "title": "总计收件？",
#                 "description": "从客户处收的件",
#             },
#             {
#                 "title": "派件中？",
#                 "description": "正在派送的件",
#             },
#             {
#                 "title": "总计妥投？",
#                 "description": "确认妥投的件",
#             },
#             {
#                 "title": "异常件?",
#                 "description": "派件员标记异常的件",
#             },
#             {
#                 "title": "收件滞留?",
#                 "description": "今天之前收件, 但是还未转交的件",
#             },
#             {
#                 "title": "派件滞留?",
#                 "description": "今天之前派件, 但是还未妥投的件",
#             },
#         ]
#         self.resp(content=content)
#
#
# class MonitorHandler(ManHandler):
#     @gen.coroutine
#     def get(self):
#         """
#         @api {get} /express/qyjl/monitor 风云app - 运单监控
#         @apiVersion 0.0.1
#         @apiName qyjl_monitor
#         @apiGroup app_qyjl
#
#         @apiSuccessExample 成功返回示例
#             HTTP/1.1 200 OK
#             body:
#                 {
#                     "today": {
#                         'total': "300", // 总数, 全部都是字符串
#                         "rate": "30.33", // 妥投率
#                         "adopted": "10", // 等待派员取件
#                         "sending": "12", // 派件员未妥投
#                         "finished": "13", // 已妥投
#                         "error": "12" // 异常件
#                     },
#                     "error": {
#                         "total": "100", // 问题件总数
#                         "user_retention": "10", // 本人滞留
#                         "courier_retention": "10", // 派件员滞留
#                         "refuse": "10", // 客户拒收
#                         "delay": "10", // 延迟派件
#                         "unreachable": "10", // 无法妥投
#                     }
#                 }
#         """
#
#         manager_id = self.man_info['id']
#         m_type = self.man_info['m_type']
#
#         start_time, end_time = TimeZone.day_range(value=TimeZone.local_now())
#         # 当日, 取今天之内取件的运单
#         params = {
#             "watcher_type": m_type,
#             "watcher_id": manager_id,
#             "time_type": "area_manager_qj_time",
#             "start_time": TimeZone.datetime_to_str(start_time),
#         }
#
#         response = yield self.async_fetch(express.redirect_aggregation_status(params))
#         data = json.loads(response.body)
#         logging.debug(data)
#         today_total = sum(data['status'].values())
#         area_manager = data.get("area_manager", {})
#         parttime = data.get("parttime", {})
#         adopted = area_manager.get(ExprState.SUB_STATUS_SENDING, 0)
#         sending = parttime.get(ExprState.SUB_STATUS_SENDING, 0)
#         finished = data['sub_status'][ExprState.SUB_STATUS_FINISHED]
#         error = data['sub_status'][ExprState.SUB_STATUS_DELAY] + data['sub_status'][ExprState.SUB_STATUS_TRASH] + \
#                 data['sub_status'][ExprState.SUB_STATUS_REFUSE]
#
#         # 历史问题件, 取今天之前取件的运单
#         params = {
#             "watcher_type": m_type,
#             "watcher_id": manager_id,
#             "time_type": "area_manager_qj_time",
#             "end_time": TimeZone.datetime_to_str(start_time),
#         }
#
#         response = yield self.async_fetch(express.redirect_aggregation_status(params))
#         data = json.loads(response.body)
#         logging.debug(data)
#         area_manager = data.get("area_manager", {})
#         parttime = data.get("parttime", {})
#         retention = area_manager.get(ExprState.SUB_STATUS_SENDING, 0)
#         courier_retention = parttime.get(ExprState.SUB_STATUS_SENDING, 0)
#         refuse = data['sub_status'][ExprState.SUB_STATUS_REFUSE]
#         delay = data['sub_status'][ExprState.SUB_STATUS_DELAY]
#         unreachable = data['sub_status'][ExprState.SUB_STATUS_TRASH]
#
#         def division(a, b):
#             a = float(a)
#             b = int(b)
#             if b == 0:
#                 return 0
#             return round((a / b) * 100, 2)
#
#         error_total = sum([retention, courier_retention, refuse, delay, unreachable])
#         rate = division(finished, today_total)
#         content = {
#             "today": {
#                 'total': today_total,
#                 "rate": rate,
#                 "adopted": adopted,
#                 "sending": sending,
#                 "finished": finished,
#                 "error": error
#             },
#             "error": {
#                 "total": error_total,
#                 "user_retention": retention,
#                 "courier_retention": courier_retention,
#                 "refuse": refuse,
#                 "delay": delay,
#                 "unreachable": unreachable,
#             }
#         }
#         self.resp(content=content)
#
#
# class ManStats(ManHandler):
#     @gen.coroutine
#     def get(self):
#         kw = Schema({
#             'my_man_id': schema_utf8,
#             'bind_time': schema_datetime,
#             'date': schema_date,
#         }).validate(self.get_query_args())
#         date = kw['date']
#         start_time, end_time = TimeZone.month_range(date.year, date.month)
#
#         # 1. 取小弟收件数
#         pipeline = [
#             # 取小弟在绑定我(作为区域经理)后内收件的运单们
#             {
#                 "$match": {
#                     "watchers.0.id": kw['my_man_id'],  # 第一个QJ的是小弟
#                     "watchers.1": {"$exists": True},  # 已经被交接: QJ+TT总数超过2
#                     "create_time": {"$gt": start_time, "$lt": end_time},  # 下单时间在给定时间范围内
#                     "times.sj_time": {"$gte": kw['bind_time']},  # 收件时间在绑定时间之后
#                 }
#             },
#             # 数一下, 获得小弟收件数
#             {
#                 "$group": {
#                     "_id": None,
#                     # "man": {"$first": {"$arrayElemAt": ["$watchers", 0]}},
#                     "expr_count": {"$sum": 1},
#                 }
#             }
#         ]
#         # logging.info(u"@@@: %s" % json.dumps(pipeline, ensure_ascii=False, indent=2, default=_dump))
#         result_sj = yield self.async_fetch(express.redirect_aggregation(pipeline=pipeline))
#         content_sj = result_sj.content
#         sj = 0
#         for c1 in content_sj:
#             # logging.info(u"%s 总计收件:%s" % (c1['_id'], c1['expr_count']))
#             sj = c1['expr_count']
#
#         # 2. 取小弟妥投数
#         pipeline = [
#             # 取小弟在绑定我(作为区域经理)后妥投并且审核通过的运单们
#             {
#                 "$match": {
#                     "status.sub_status": "FINISHED",  # 取正常妥投的
#                     "assignee.id": "56c2e7d97f4525452c8fc23c",  # 是这个小弟妥投的
#                     "create_time": {"$gt": start_time, "$lt": end_time},  # 下单时间在给定时间范围内
#                     # 审核通过的,即截至3天前妥投的
#                     "times.parttime_tt_time": {"$gte": kw['bind_time'], "$lt": TimeZone.decrement_days(end_time, 3)},
#                 }
#             },
#             # 数一下, 获得小弟妥投数
#             {
#                 "$group": {
#                     "_id": None,
#                     "name": {"$first": "$assignee.name"},
#                     "expr_count": {"$sum": 1},
#                 }
#             }
#         ]
#         # logging.info(u"@@@: %s" % json.dumps(pipeline, ensure_ascii=False, indent=2, default=_dump))
#         result_tt = yield self.async_fetch(express.redirect_aggregation(pipeline=pipeline))
#         content_tt = result_tt.content
#         tt = 0
#         name = ''
#         for c2 in content_tt:
#             # logging.info(u"%s 总计妥投:%s" % (c2['name'], c2['expr_count']))
#             tt = c2['expr_count']
#         logging.info(u"%s 总计收件:%s, 总计妥投:%s" % (name, sj, tt))
#         self.resp({'sj_count': sj, 'tt_count': tt})
#
#
# class ExpressHandler(ManHandler):
#     @gen.coroutine
#     def get(self):
#         """
#             @api {get} /express/qyjl/multi 风云app专用 - 运单列表和运单搜索
#             @apiName qyjl_multi
#             @apiGroup app_qyjl
#             @apiVersion 0.0.1
#
#             @apiParam (query param) {string} start_time 开始时间
#             @apiParam (query param) {string} end_time 结束时间
#             @apiParam (query param) {string="sj_total","not_transfer","sending","finished","error","sj_delay","pj_delay"} query_type 结束时间
#             @apiParam (query param) {int} [page] 分页号
#             @apiParam (query param) {int} [count] 每页的个数
#             @apiParam (query param) {int} [limit] 是否分页
#             @apiParam (query param) {string} [limit] 是否分页
#             @apiParam (query param) {string} [includes] 需要的字段
#             @apiParam (query param) {string} [excludes] 不需要的字段
#             @apiParam (query param) {string} [only] 只想要的字段
#
#             @apiSuccessExample 成功返回示例
#             HTTP/1.1 200 OK
#             [
#                 {express}, ...
#             ]
#             @apiUse default_express
#             @apiUse bad_response
#         """
#         try:
#             data = Schema({
#                 "start_time": schema_datetime,
#                 "end_time": schema_datetime,
#                 "query_type": And(schema_utf8, lambda x: x in (
#                     "sj_total", "not_transfer", "sending", "finished", "error", "sj_delay", "pj_delay"
#                 )),
#                 Optional("page"): schema_int,
#                 Optional("count"): schema_int,
#                 Optional("limit"): schema_bool,
#                 Optional("includes"): schema_utf8_multi,
#                 Optional("excludes"): schema_utf8_multi,
#                 Optional("only"): schema_utf8_multi,
#                 Optional("order_by"): schema_utf8_multi,
#             }).validate(self.get_query_args())
#             start_time = data.pop("start_time")
#             end_time = data.pop("end_time")
#             query_type = data.pop("query_type")
#         except Exception:
#             self.resp_args_error()
#             return
#
#         man_list = yield get_bind_man(self.man_info['id'])
#         q = Q()
#
#         m_type = "parttime"
#         day_start, _ = TimeZone.day_range(value=TimeZone.local_now())
#
#         builder_map = {
#             "sj_total": QueryBuilder.sj,
#             "not_transfer": QueryBuilder.not_zj,
#             "sending": QueryBuilder.sending,
#             "finished": QueryBuilder.finished,
#             "error": QueryBuilder.error,
#             "sj_delay": QueryBuilder.not_zj,
#             "pj_delay": QueryBuilder.sending,
#         }
#         builder = builder_map[query_type]
#
#         for man in man_list:
#             man_id = man['man_id']
#             bind_time = TimeZone.str_to_datetime(man['bind_time'])
#             start, end = None, None
#             if bind_time > end_time and query_type in ("sj_total", "not_transfer", "sending", "finished"):
#                 # 绑定时间在查询时间之后的不显示
#                 continue
#             if bind_time > day_start and query_type in ("sj_delay", "pj_delay"):
#                 # 绑定时间在今天之前的, 在上述两个类型中不显示
#                 continue
#             if query_type in ("sj_total", "not_transfer", "sending", "finished"):
#                 start = bind_time if bind_time > start_time else start_time
#                 end = end_time
#             if query_type == "error":
#                 start = bind_time
#                 end = None
#             if query_type in ("sj_delay", "pj_delay"):
#                 start = bind_time
#                 end = day_start
#
#             q |= Q(**builder(man_id, m_type, start, end))
#
#         # 有可能会出现查询条件为空的情况
#         if q.empty:
#             self.set_header('X-Resource-Count', 0)
#             self.resp(content=[])
#             return
#
#         data.update({
#             "Q": q
#         })
#
#         yield self.resp_redirect(express.redirect_pickle_search(data))
