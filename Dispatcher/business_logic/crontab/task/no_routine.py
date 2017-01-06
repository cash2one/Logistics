#!/usr/bin/env python
# coding:utf-8
"""
报错统计：每日将所有报错为未找到合适路线的订单导出为excel并发送到指定邮箱
"""
from __future__ import unicode_literals
import json
import arrow
import logging
from utils import once, expr_conn, mongodb_client, send_mail
from tools_lib.bl_expr import ExprState


once("报错路线的订单导出", days=0)
def export_bad_express():
    aggr_to_run = [
    # Stage 1
    {
      "$match": {
        'create_time': {"$gte":  arrow.now().to("local").isoformat()},
        'msg': '未查询到合适路线'
      }

    },

    # Stage 2
    {
      "$group": {
      "_id": '$number'
      }
    },
  ]
    ret = expr_conn.aggregate(aggr_to_run)
    return