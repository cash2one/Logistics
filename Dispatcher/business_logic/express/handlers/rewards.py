# #! /usr/bin/env python
# # coding: utf-8
# import logging
# import pickle
#
# from models import Rewards
# from mongoengine import Q
# from schema import Optional, Schema
# from tools_lib.gmongoengine.paginator import paginator
# from tools_lib.gtornado.escape import schema_int, schema_bool
# from tools_lib.gtornado.web2 import ReqHandler
# from tornado import gen
#
#
# class PickleSearchHandler(ReqHandler):
#     @gen.coroutine
#     def post(self):
#         try:
#             data = pickle.loads(self.request.body)
#
#             data = Schema({
#                 Optional(object): object,
#                 Optional("Q", default=Q()): object,
#                 Optional("page", default=1): schema_int,
#                 Optional("count", default=20): schema_int,
#                 Optional("limit", default=1): schema_bool,
#
#                 Optional("includes", default=None): list,
#                 Optional("excludes", default=None): list,
#                 Optional("only", default=None): list,
#                 Optional("order_by", default=['-update_time']): list,
#             }).validate(data)
#
#             page = data.pop('page')
#             count = data.pop('count')
#             limit = data.pop('limit')
#             includes = data.pop('includes')
#             excludes = data.pop('excludes')
#             only = data.pop('only')
#             order_by = data.pop('order_by')
#             query = data.pop("Q")
#
#         except Exception as e:
#             logging.exception(e.message)
#             self.resp_args_error()
#             return
#         try:
#             q = Q(**data) & query
#             logging.debug(q.to_query(Rewards))
#             count, rewards_list = paginator(Rewards.objects(q).order_by(*order_by), page, count, limit)
#         except Exception:
#             logging.exception(data)
#             self.resp_args_error()
#             return
#
#         self.set_header('X-Resource-Count', count)
#         self.resp([rewards.pack(includes=includes, excludes=excludes, only=only)
#                    for rewards in rewards_list])
#
#
# class AggregationHandler(ReqHandler):
#     @gen.coroutine
#     def post(self):
#         try:
#             pipeline = pickle.loads(self.request.body)
#         except Exception as e:
#             logging.exception(e.message)
#             self.resp_args_error(e.message)
#             return
#         result = Rewards.objects.aggregate(*pipeline)
#
#         content = [doc for doc in result]
#         self.resp(content=content)
