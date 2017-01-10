# coding:utf-8


import json
import pickle

import settings

from .config import async_cli, timeouts, xls_create_expr_timeouts
from tools_lib.common_util import sstring
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.windchat import http_utils
from tornado.gen import coroutine, Return
from tornado.httpclient import HTTPRequest
from tornado.httputil import url_concat


# === FH-APP/H5/SONG/YUN 通用 ===
# == 列表/查询
def redirect_query_express(**kwargs):
    """
    [HTTPRequest]运单查询
    """
    url = settings.BL_DAS_API_PREFIX + "/express/expr"
    url = url_concat(url, kwargs)
    return HTTPRequest(
        url,
        method="GET",
        **timeouts
    )


# == 更强大的列表/查询
def redirect_pickle_search(query):
    url = settings.BL_DAS_API_PREFIX + "/express/expr/search"
    return HTTPRequest(
        url,
        method="POST",
        body=pickle.dumps(query),
        **timeouts
    )


# == 聚合查询
def redirect_aggregation(query=None, pipeline=None):
    url = settings.BL_DAS_API_PREFIX + "/express/aggregation"
    url = url_concat(url, query)
    return HTTPRequest(
        url,
        method="POST",
        body=pickle.dumps(pipeline),
        **timeouts
    )


# == 按状态聚合查询
def redirect_aggregation_status(query):
    url = settings.BL_DAS_API_PREFIX + "/express/aggregation/status"
    url = url_concat(url, query)
    return HTTPRequest(
        url,
        method="GET",
        **timeouts
    )


# == 运单详情
def redirect_get_express(number, **kwargs):
    """
    [HTTPRequest]一个运单的详情
    """
    url = settings.BL_DAS_API_PREFIX + "/express/expr/single/" + sstring.safe_unicode(number)
    url = url_concat(url, kwargs)
    return HTTPRequest(
        url,
        method="GET",
        **timeouts
    )


# === FH-APP/H5 ===
# == 一键呼叫
def redirect_one_key_call(shop, count):
    url = settings.BL_DAS_API_PREFIX + '/express/call'
    body = {
        'shop': shop,
        'count': count
    }
    return HTTPRequest(
        url,
        method='POST',
        body=json.dumps(body),
        headers={'Content-Type': 'applications/json'},
        **timeouts
    )


# == 一键呼叫列表
def redirect_query_one_key_call(query):
    url = settings.BL_DAS_API_PREFIX + '/express/call/search'
    return HTTPRequest(
        url,
        method="POST",
        body=pickle.dumps(query),
        **timeouts
    )


# == 呼叫内的客户运单列表: 任务--收件--立即前往--客户运单
def redirect_query_call_expr_list(query):
    url = settings.BL_DAS_API_PREFIX + '/express/call/expr_list'
    url = url_concat(url, query)
    return HTTPRequest(
        url,
        method='GET',
        **timeouts
    )


# == 运单操作: 余额支付
def redirect_perform_pay(shop_id, cash, number_list):
    url = settings.BL_DAS_API_PREFIX + "/express/pay"
    kw = dict(shop_id=shop_id, cash=cash, number_list=number_list)
    return HTTPRequest(url,
                       method="PATCH",
                       body=json.dumps(kw),
                       **timeouts)


# === PS-APP ===
# == 领取运单
def redirect_assign_to_me(data):
    url = settings.BL_DAS_API_PREFIX + "/express/assign_to_me"
    return HTTPRequest(
        url,
        method="PATCH",
        body=json.dumps(data),
        headers={"Content-Type": "application/json"},
        **timeouts
    )


# == 修改运费
def redirect_modify_fee(number, data):
    url = settings.BL_DAS_API_PREFIX + "/express/expr/fee"
    data['number'] = number
    return HTTPRequest(
        url,
        method="PATCH",
        body=json.dumps(data),
        headers={"Content-Type": "application/json"},
        **timeouts
    )


# == 派件员发起收款: 批量完成定价状态变迁, 不会去改运费!!
def redirect_multi_pricing(data):
    url = settings.BL_DAS_API_PREFIX + "/express/multi/pricing"
    return HTTPRequest(
        url,
        method="PATCH",
        body=json.dumps(data),
        headers={"Content-Type": "application/json"},
        **timeouts
    )


# 操作来源
OPERATOR_TYPE_INSIDE = "INSIDE"  # 内部操作
OPERATOR_TYPE_OUTSIDE = "OUTSIDE"  # 外部操作(通常都是外部操作)


# == 呼叫操作: 立即响应(抢呼叫)/ 关闭呼叫入口/ 加单(打印,定价)/ 生成收款码/ 收件
def redirect_perform_call_event(call_id, operator_type=OPERATOR_TYPE_OUTSIDE, **kwargs):
    url = settings.BL_DAS_API_PREFIX + '/express/call/single/%s' % call_id
    kwargs['operator_type'] = operator_type
    return HTTPRequest(
        url,
        method='PATCH',
        body=json.dumps(kwargs),
        **timeouts
    )


# == 运单派件操作: 取消/取件/入仓/妥投/延迟配送/拒收/无法投递
def redirect_perform_expr_event(number, operator_type=OPERATOR_TYPE_OUTSIDE, **kwargs):
    url = settings.BL_DAS_API_PREFIX + '/express/expr/single/%s' % (number,)
    kwargs['operator_type'] = operator_type
    return HTTPRequest(
        url,
        method='PATCH',
        body=json.dumps(kwargs),
        **timeouts
    )


# == 根绝商户id或者呼叫id,模糊查找收货、发货地址
def redirect_search_client_address(term, search_in, shop_id="", call_id=""):
    """
    [HTTPRequest]搜索收货发货地址
    """
    url = settings.BL_DAS_API_PREFIX + "/express/client_address/fuzzy_search"
    url = url_concat(url, {
        'shop_id': shop_id,
        'call_id': call_id,
        "term": term,
        "search_in": http_utils.list_to_dot_string(search_in)
    })
    return HTTPRequest(
        url,
        method="GET",
        **timeouts
    )


# === song.123feng.com ===
# == 批量下单(填信息下单): 返回请求
def redirect_bulk_create_express(creator, expr_list, pay=False):
    """
    [HTTPRequest]批量创建运单
    :param creator: 下单者,商户
    :param expr_list: 运单dict的list
    :param pay: 是否需要付款
    """
    url = settings.BL_DAS_API_PREFIX + "/express/expr"
    real_body = {
        "creator": creator,
        "expr_list": expr_list,
        "pay": pay
    }
    return HTTPRequest(
        url,
        method="POST",
        body=json.dumps(real_body),
        headers={"Content-Type": "application/json"},
        **xls_create_expr_timeouts
    )


# == 批量下单(填信息下单): 返回异步结果
@coroutine
def bulk_create_express(*args, **kwargs):
    """
    批量创建运单
    :return: _content, _message, _http_code
    """
    resp = yield async_cli.fetch(redirect_bulk_create_express(*args, **kwargs), raise_error=False)
    body_dict = json.loads(resp.body)
    _content = body_dict.get("content")
    _message = body_dict.get("message")
    _http_code = resp.code
    raise Return((_content, _message, _http_code))


def redirect_song_export_express(creator_id, start_time, end_time):
    """
    [HTTPRequest]SONG导出运单信息
    :param creator: 下单者id,商户id
    :param start_time: 起始时间
    :param end_time: 终止时间
    """
    url = settings.BL_DAS_API_PREFIX + "/express/export/song"
    url = url_concat(url, {
        "shop_id": creator_id,
        "start_time": TimeZone.datetime_to_str(start_time),
        "end_time": TimeZone.datetime_to_str(end_time)
    })
    return HTTPRequest(
        url,
        method="GET",
        **timeouts
    )


# == 根据id获取人员签到列表
def redirect_get_my_schedule(man_id):
    """
    [HTTPRequest]运单查询
    """
    url = settings.BL_DAS_API_PREFIX + "/express/schedule"
    url = url_concat(url, {'id': man_id})
    return HTTPRequest(
        url,
        method="GET",
        **timeouts
    )


