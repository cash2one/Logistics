# coding:utf-8


import decimal
import functools
import json
import logging
import pickle
from ast import literal_eval

import requests
from schema import Schema, Optional
from tools_lib.transwarp.escape import (schema_unicode_empty, schema_int, schema_unicode, schema_float,
                                        schema_unicode_multi)
from tools_lib.transwarp.tz import utc_8_to_utc
from tools_lib.transwarp.web import api, ctx, get, post, Dict, process_err, dumps

# from tools_lib.das_api import get_man_info_from_token, get_shop_info_from_token, get_shop_info_from_kwargs
from tools_lib.common_util.third_party.image import get_up_token
from config import CONFIGS, BL_DAS_PORT, TIMEOUT, DEBUG
from tools_lib.java_account import SyncAccount

"""
@apiDefine AuthHeader

@apiHeaderExample Auth-Header-Example
    {
        "Authorization": "token 5b42e18555c11dbf2c31403ea6b706a6"
    }
@apiHeader {string} Authorization 验证身份，格式为"token <token>"，注意"token"后面需要一个空格
"""

# INIT
das_man = CONFIGS.man_host
das_shop = CONFIGS.shop_host
bl_express = CONFIGS.express_host
urls = Dict(**{
    # 派件员相关 #
    "man_sms": das_man + "/deliveryman/sms_code",
    "man_complex_query": das_man + "/deliveryman/complex_query",
    "man_login": das_man + "/deliveryman/login",
    "man_operation": das_man + "/deliveryman/{operation}",
    "man_get_what": das_man + "/deliveryman/outsource/get/{what}",
    "man_fsm": das_man + "/deliveryman/fsm_log/complex_query",
    # 工作关系相关
    "man_bind_manager": das_man + "/deliveryman/working_relation/bind_manager",
    "man_apply_unbind_manager": das_man + "/deliveryman/working_relation/apply_unbind_manager",
    "man_del_man": das_man + "/deliveryman/working_relation/del_man",
    # 签到
    "man_sign_in": das_man + "/deliveryman/sign_in",
    # 派件员提现相关
    "flow_statistics": das_man + "/deliveryman/flow_statistics/complex_query",
    "flow_apply_withdraw": das_man + "/deliveryman/outsource/APPLY_WITHDRAW",
    "flow": das_man + "/deliveryman/flow/complex_query",
    "flow_paid": das_man + "/deliveryman/outsource/PAID",
    "flow_decline": das_man + "/deliveryman/outsource/DECLINE",

    # 商户相关 #
    "shop_sms": das_shop + "/shop/sms_code",
    "shop_complex_query": das_shop + "/shop/complex_query",
    "shop_operation": das_shop + "/shop/fsm/{operation}",
    "shop_login": das_shop + "/shop/login",
    "shop_web_top_up": das_shop + "/shop/web_top_up",
    "shop_app_top_up": das_shop + "/shop/app_top_up",
    "shop_wap_top_up": das_shop + "/shop/wap_top_up",
    "js_sdk_signature": das_shop + "/shop/h5/js_sdk_signature",
    "shop_h5_wx_top_up": das_shop + "/shop/h5/wx_top_up",
    "shop_web_app_top_up_callback": das_shop + "/shop/web_app_top_up_callback",
    "shop_wap_top_up_callback": das_shop + "/shop/wap_top_up_callback",
    "shop_h5_wx_top_up_callback": das_shop + "/shop/wx_top_up_callback",
    "shop_native_wx_pay_callback": das_shop + "/shop/native/wx_pay_callback",
    "shop_native_alipay_callback": das_shop + "/shop/native/alipay_callback",
    "pay_call_back_notify_first_success": bl_express + "/express/pay/call_back/notify_first_success",
    "check_shop_transact": das_shop + "/shop/check_transact",
    "shop_cash_flow": das_shop + "/shop/cash_flow",
    "shop_balance": das_shop + "/shop/flow_statistics/complex_query",
    "shop_expense": das_shop + "/shop/flow_statistics/complex_query",
    "shop_flow": das_shop + "/shop/flow/complex_query",

})
logging.info("Related Deliveryman Service: %s" % das_man)
# ===> 用唯一的线上测试员 <===
QA = {'13245678901': '',
      '15058115878': '庄兵', '18368850370': '洪武',
      '15850537730': '兆华', '18679401681': '海叶',
      '18868804355': '征原'}
# ===> 以下为派件员相关操作 <===
APP_EVENTS = Dict(**{k: k for k in ('ADD_ACCOUNT', 'ADD_FAMILIAR', 'DEL_FAMILIAR', 'ADD_PICKUP', 'DEL_PICKUP',
                                    'EVENT_COMPLETE_INFO')})
FE_EVENTS = Dict(**{k: k for k in ('EVENT_RESET', 'EVENT_BAN',
                                   'EVENT_COMPLETE_INFO', 'EVENT_HR_DECIDE_INFO_MISTAKEN', 'EVENT_HR_DECIDE_YES')})
# ("VALIDATED", "APPLY_WITHDRAW", "PAID", "DECLINE")
WHATS = Dict(**{x: x for x in ("BASIC", "STATUS", "ACCOUNT_LIST", "FAMILIAR_LIST", "CODE", "MAN_LIST", "PICKUP_LIST")})

# ===> 以下为商户相关操作 <===
OUTSIDE_EVENTS = Dict(**{k: k for k in ('EVENT_ACK_INFO_NO', 'EVENT_COMPLETE_INFO', 'EVENT_ACK_INFO_YES')})
FE_INSIDE_EVENTS = Dict(**{k: k for k in (
    'EVENT_ALTER_INFO', 'EVENT_RESET', 'EVENT_HR_DECIDE_INFO_MISTAKEN', 'EVENT_HR_DECIDE_YES', 'EVENT_BAN')})


def api_with_deliveryman_auth(func):
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        man = {}
        try:
            # 权限检查
            auth = ctx.request.header('Authorization')
            man = SyncAccount.get_basic_from_token({'Authorization': auth})
            if not man:
                resp = None
                ctx.response.status = '401 Unauthorized'
            else:
                kw['man'] = man
                resp = dumps(func(*args, **kw))
        except Exception as err:
            resp = process_err(err, man=man)
        ctx.response.content_type = 'application/json'
        ctx.response.content_length = len(resp) if resp else 0
        return resp

    _wrapper.orig = func
    return _wrapper


def api_with_shop_auth(func):
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        shop = {}
        try:
            auth = ctx.request.header('Authorization')
            shop = SyncAccount.get_basic_from_token({'Authorization': auth})
            if shop:
                kw['shop_id'] = shop['id']
                resp = dumps(func(*args, **kw))
            else:
                resp = None
                ctx.response.status = '401 Unauthorized'
        except Exception as err:
            resp = process_err(err, shop=shop)
        ctx.response.content_type = 'application/json; charset=utf8'
        ctx.response.content_length = len(resp) if resp else 0
        return resp

    _wrapper.orig = func
    return _wrapper


def process_bl_response(requests_resp_obj):
    if requests_resp_obj.status_code == 204:
        ctx.response.status = 204
        return
    elif requests_resp_obj.status_code != 200 and requests_resp_obj.status_code != 404:
        msg = json.loads(requests_resp_obj.text)["message"]
        if msg.find("already added") != -1:
            msg = "请勿重复添加"
        raise ValueError(msg)
    elif requests_resp_obj.status_code == 404:
        raise ValueError("404 Not Found")
    bl_resp = requests_resp_obj.json()
    return bl_resp


def process_alipay_top_up_resp_obj(requests_resp_obj):
    if requests_resp_obj.status_code != 200:
        msg = json.loads(requests_resp_obj.text)["message"]
        raise ValueError(msg)
    else:
        ctx.response.content_type = 'text/plain'
        return requests_resp_obj.text  # 'success'


def process_wxpay_resp_obj(requests_resp_obj):
    if requests_resp_obj.status_code != 200:
        msg = json.loads(requests_resp_obj.text)["message"]
        raise ValueError(msg)
    else:
        ctx.response.content_type = 'text/xml'
        return requests_resp_obj.json()  # {'ret': <xml>...</xml>, 'msg': ''}


@api
@get('/port')
def api_get_prod_port():
    """
    只是为了给Nginx那台机器找线上BL/DAS的端口用.
    :return:
    """
    return BL_DAS_PORT


@api
@get('/other/uptoken')
def api_get_other_uptoken():
    """
    拿七牛上传token, 给前端用.
    """
    kw = ctx.request.input()
    return get_up_token(key=kw.get('key'))


# ===> (对外)人员基本信息相关: 验证码,注册,登录,修改资料 <===
@api
@get('/deliveryman/sms_code')
def api_man_sms_code():
    """
    @api {get} /deliveryman/sms_code [派件员]获取验证码
    @apiName api_man_sms_code
    @apiGroup app_deliveryman

    @apiParam {string(11)} [tel] 用于接受验证码的手机号, 如 13245678901.

    @apiParamExample {json} 请求url/param示例:
    Request Method: GET
    Request URL: http://182.92.240.69:5000/deliveryman/sms_code?tel=13245678901
    @apiSuccessExample {json} 获取验证码成功示例:
        HTTP/1.1 200 OK
        {}
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
          "message": "error msg."
        }
    """
    url = urls["man_sms"]
    param = ctx.request.input()
    # 如果是QA,不发验证码.
    if not DEBUG and param.tel in list(QA.keys()):
        raise ValueError("检测到%s尝试获取PROD验证码.请用【13245678901:123456】登录." % QA[param.tel])
    resp = requests.get(url, params=param, timeout=TIMEOUT)
    process_bl_response(resp)


@api
@get('/deliveryman/log_in')
def api_deliveryman_login():
    """
    @api {get} /deliveryman/log_in [派件员/员工]登录
    @apiDescription 风先生派件员/职能员工登录成功则返回token,失败则报错.
    @apiName api_deliveryman_login
    @apiGroup app_deliveryman

    @apiParam {string(11)} tel 手机号, 如 150687929321.
    @apiParam {string(32)} password 验证码/密码.
    @apiParam {string(32)} [role] `staff`/`man`. 默认`man`.

    @apiParamExample {json} 派件员登录示例:
    Request Method: GET
    Request URL: http://dev.api.mrwind.com:5000/deliveryman/log_in?tel=150687929321&password=123456
    @apiParamExample {json} 职能员工登录示例:
    Request Method: GET
    Request URL: http://dev.api.mrwind.com:5000/deliveryman/log_in?tel=13245678901&password=e10adc3949ba59abbe56e057f20f883e&role=staff
    @apiSuccessExample {json} 手机号验证码登录成功示例:
        HTTP/1.1 200 OK
        {
            "jd": "city_driver",
            "man_id": "56c2e7d97f4525452c8fc23c",
            "tel": "13245678901",
            "token": "0646e97552d30c1b2953eaef7ed744f5"
        }
    @apiSuccessExample {json} 手机号密码登录成功示例(暂时没用):
        HTTP/1.1 200 OK
        {
            "man_id": "56c2e7d97f4525452c8fc23c",
            "token": "0646e97552d30c1b2953eaef7ed744f5"
        }
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
          "message": "登录失败:验证码验证失败."
        }
    """
    url = urls["man_login"]
    params = ctx.request.input()
    resp = requests.get(url, params=params, headers=ctx.request.headers, timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_deliveryman_auth
@post('/deliveryman/create_or_update/:app_operation')
def api_update_deliveryman(operation, man):
    """
    @api {post} /deliveryman/create_or_update/:OPERATION [派件员]更新
    @apiDescription 派件员添加支付宝;添加/删除送单区域;完善资料.
    @apiName api_update_deliveryman
    @apiGroup app_deliveryman

    @apiParam {str} OPERATION URI中: 限定URI接口操作,可选值: `add_account`/`add_familiar`/`del_familiar`/`event_complete_info`.
    @apiParamExample {json} add_account请求示例:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/create_or_update/add_account
        Request Method: POST
        Request Payload:
        {
            "name": "测试爱丽丝",
            "id": "alipay account id"
        }
    @apiParamExample {json} add_familiar/del_familiar请求示例:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/create_or_update/add_familiar
        OR http://dev.api.mrwind.com:5000/deliveryman/create_or_update/del_familiar
        Request Method: POST
        Request Payload:
        {
            "city": "杭州",
            "district": "拱墅区",
            "addr": "2号大街3号路口杭州电子科技大学-学生生活区3号楼402",
            "lat": "30.218152",
            "lng": "120.22262"
        }
    @apiParamExample {json} event_complete_info请求示例:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/create_or_update/event_complete_info
        Request Method: POST
        Request Payload:
        {
            "id_card_num": "123456789012345678",
            "name": "测试1号",
            "avatar": "AF9650D87988D915577E4130422187CE",
            "id_card_back": "AF9650D87988D915577E4130422187CE"
        }
    @apiSuccessExample {str} 成功示例:
        HTTP/1.1 200 OK
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
            "message": "Already added."
        }
    @apiError (错误码) 401 Token错误
    @apiError (错误码) 400 重复添加或其他逻辑错误.
    """
    operation = str(operation).upper().strip()
    kw = ctx.request.input()
    # 对完善资料额外做参数校验
    if operation == APP_EVENTS.EVENT_COMPLETE_INFO:
        kw = Schema({
            'id_card_num': schema_unicode,
            'name': schema_unicode,
            'avatar': schema_unicode,
            'id_card_back': schema_unicode,
            Optional('recommended_by'): {
                'tel': schema_unicode_empty
            },
        }).validate(kw)
    if operation in APP_EVENTS:
        url = urls["man_operation"].format(operation=operation)
        kw['man_id'] = str(man['man_id'])
        kw['operator_type'] = 'APP'
        resp = requests.post(url, json=kw, timeout=TIMEOUT)
        return process_bl_response(resp)
    else:
        raise ValueError("operation[%s] to be supported~" % operation)


@api_with_deliveryman_auth
@get('/deliveryman/outsource/get/can_cash')
def api_outsource_get_can_cash(man):
    """
    @api {get} /deliveryman/outsource/get/:WHAT [派件员]查询提现
    @apiDescription 查询派件员提现相关的信息: 获取提现列表;获取可提现金额;获取支付宝帐号列表.
    @apiName api_outsource_get_info
    @apiGroup app_deliveryman

    @apiParam {str} WHAT URI中: 限定URI接口返回信息,可选值: `applied_withdraw`/`can_cash`/`account_list`.
    @apiParamExample {json} applied_withdraw请求url示例:
        GET /deliveryman/outsource/get/applied_withdraw
    @apiParamExample {json} can_cash请求url示例:
        GET /deliveryman/outsource/get/can_cash
    @apiParamExample {json} account_list请求url示例:
        GET /deliveryman/outsource/get/account_list
    @apiSuccessExample {json} applied_withdraw成功示例:
        HTTP/1.1 200 OK
        [
            {
                "transact_num": "20160121189599",
                "cash": 500,
                "account_id": "alipay id",
                "account_name": "alipay name",
                "status": "APPLY_WITHDRAW/PAID/DECLINE"
                "create_time": "2016-1-21 18:08:08"
            }
            ...
        ]
    @apiSuccessExample {int} can_cash成功示例:
        HTTP/1.1 200 OK
        500
    @apiSuccessExample {json} account_list成功示例:
        HTTP/1.1 200 OK
        [
            {
                "id" : "alipay account id",
                "name" : "测试爱丽丝"
            },
            ...
        ]
    @apiSuccess (OK 200) {str} transact_num 提交成功的申请交易号
    @apiSuccess (OK 200) {str} status `APPLY_WITHDRAW`申请中/`PAID`已打款/`DECLINE`财务扣款
    """
    # 用真正的man_id去查询
    url = urls['flow_statistics']
    query = {
        "filter_col": [],
        "query":
            {
                "op": "AND",
                "exprs": [
                    {"man_id": {"=": man['man_id']}}
                ]
            }
    }
    resp = requests.post(url, json=query, timeout=TIMEOUT)
    flow_stats = process_bl_response(resp)
    if not flow_stats:
        return 0
    else:
        stat = flow_stats[0]
        return stat["can_cash"]


@api_with_deliveryman_auth
@get('/deliveryman/outsource/get/account_list')
def api_outsource_get_accounts(man):
    url = urls['man_get_what'].format(what='account_list')
    resp = requests.get(url, params=dict(id=man['man_id']), timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_deliveryman_auth
@post('/deliveryman/outsource/apply_withdraw')
def api_outsource_apply_withdraw(man):
    """
    @api {post} /deliveryman/outsource/apply_withdraw [派件员]申请提现
    @apiDescription 派件员在APP端申请提现.
    @apiName api_outsource_apply_withdraw
    @apiGroup app_deliveryman
    @apiParamExample {json} 请求示例:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/outsource/apply_withdraw
        Request Method: POST
        Request Payload:
        {
            "cash": 50,
            "account_name": "测试艾利斯",
            "account_id": "支付宝id"
        }
    @apiSuccessExample {str} 成功示例:
        HTTP/1.1 200 OK
        "20160310QLuQgx"
    @apiSuccess (OK 200) {str} transact_num 提交成功的申请交易号
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
            "message": "You are not allowed to apply for cash over [50] yuan."
        }
    @apiError (错误码) 401 Token错误
    @apiError (错误码) 400 提现超额或其他逻辑错误.
    """
    url = urls["flow_apply_withdraw"]
    body = ctx.request.input()
    body['man_id'] = man['man_id']
    resp = requests.post(url, json=body, timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_deliveryman_auth
@get('/deliveryman/outsource/get/applied_withdraw')
def api_outsource_get_applied_withdraw(man):
    # 用真正的man_id去查
    url = urls['flow']
    body = {
        "filter_col": ["type", "transact_num", "account_id", "account_name", "cash", "create_time"],
        "query":
            {
                "op": "AND",
                "exprs": [
                    {"man_id": {"=": man['man_id']}},
                    {"type": {"in": ["APPLY_WITHDRAW", "PAID", "DECLINE"]}}
                ]
            },
        "order_by": "type,create_time desc"
    }
    resp = requests.post(url, json=body, params=ctx.request.input(), timeout=TIMEOUT)
    flows = process_bl_response(resp)
    for f in flows:
        f['create_time'] += '+0800'
    return flows


@api_with_deliveryman_auth
@get('/deliveryman/get/basic')
def api_man_get_basic(man):
    url = urls['man_get_what'].format(what='basic')
    resp = requests.get(url, params=dict(id=man['man_id']), timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_deliveryman_auth
@get('/deliveryman/get/status')
def api_man_get_status(man):
    url = urls['man_get_what'].format(what='status')
    resp = requests.get(url, params=dict(id=man['man_id']), timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_deliveryman_auth
@get('/deliveryman/get/remark')
def api_man_get_remark(man):
    """
    @api {get} /deliveryman/get/remark [派件员]后台备注
    @apiDescription 查询派件员审核资料后的后台备注(如有).
    @apiName api_man_get_remark
    @apiGroup app_deliveryman

    @apiParamExample {json} 请求示例:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/get/remark
        Request Method: GET
    @apiSuccessExample {str} 成功示例:
        HTTP/1.1 200 OK
        "测试上帝操作"
    @apiSuccess (200 OK) {str} remark 后台修改建议
    """
    query = {
        "filter_col": ["remark"],
        "query":
            {
                "op": "AND",
                "exprs": [
                    {"man_id": {"=": man['man_id']}}
                ]
            },
        "order_by": "id DESC",
        "count": 1
    }
    url = urls["man_fsm"]
    resp = requests.post(url, json=query, timeout=TIMEOUT)
    ret = process_bl_response(resp)
    return ret[0] if ret else ""


@api_with_deliveryman_auth
@get('/deliveryman/get/familiar_list')
def api_man_get_familiars(man):
    """
    @api {get} /deliveryman/get/familiar_list [派件员]送单区域
    @apiDescription 查询派件员送单区域列表.
    @apiName api_man_get_familiars
    @apiGroup app_deliveryman

    @apiParamExample {json} 请求示例:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/get/familiar_list
        Request Method: GET
    @apiSuccessExample {json} 成功示例:
        HTTP/1.1 200 OK
        [
            {
                "lat": "30.218152",
                "lng": "120.22262",
                "city": "杭州",
                "addr": "拱墅莫干山路武林巷口易盛大厦11楼（电梯出来右走到底）纺织网",
                "district": "拱墅区"
            },
            ...
        ]
    @apiSuccess (200 OK) {str} lat 该送单区域纬度
    @apiSuccess (200 OK) {str} lng 该送单区域经度
    """
    url = urls['man_get_what'].format(what='familiar_list')
    resp = requests.get(url, params=dict(id=man['man_id']), timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_deliveryman_auth
@get('/deliveryman/search/shop')
def api_man_outside_search_shop(man):
    url = urls['shop_complex_query']
    kw = Schema({
        Optional('term'): schema_unicode_empty,
        Optional('page'): schema_int,
        Optional('count'): schema_int,
    }).validate(ctx.request.input())
    term = kw.get('term', '')

    query = {
        "status": {"$in": ["STATUS_INFO_YES", "STATUS_VALID"]},
        "$or": [
            {"tel": {"$regex": ".*%s.*" % term}},
            {"name": {"$regex": ".*%s.*" % term}}
        ]
    }
    query = dict(query=pickle.dumps(query))

    if 'page' in kw:
        query['page'] = kw['page']
    if 'count' in kw:
        query['count'] = kw['count']
    query['only'] = ['name', 'id']
    resp = requests.post(url, json=query, timeout=TIMEOUT)
    d = resp.json()
    if not d:
        d = []
    elif isinstance(d, dict):
        d = [d]
    ctx.response.set_header("X-Resource-Count".encode('utf-8'), resp.headers.get('X-Resource-Count', '0'))
    return d


# ===> 签到 <===
@api_with_deliveryman_auth
@post('/deliveryman/sign_in')
def api_man_sign_in(man):
    """
    签到.
    需要parse成这样传入DAS:
    {
        "man_id": "56c2e7d97f4525452c8fc23c",
        "loc":{
            "name": "短地址名",
            "addr": "详细地址",
            "lng": 102.3444,
            "lat": 23.3312
        },
        "device": {
            # "mac_id": "ff02::2:ff33:9cc0"
        }
    }
    :param man:
    :return: 签到成功时间 {"create_time": "2016-05-06T14:47:49"}
    """
    url = urls['man_sign_in']
    kw = Schema({
        "loc": {
            "name": schema_unicode_empty,
            "addr": schema_unicode,
            "lng": schema_float,
            "lat": schema_float,
        },
        "device": {
            Optional("mac_id"): schema_unicode_empty,
            Optional("model"): schema_unicode
        },
        # Optional(object): object
    }).validate(ctx.request.input())
    # 限制: 审核未通过不能签到
    if man['status'] != 'STATUS_WORKING':
        raise ValueError('请先认证资料或等待审核通过')
    kw['man_id'] = man['man_id']
    resp = requests.post(url, json=kw, timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_deliveryman_auth
@get('/deliveryman/get/sign_in_count')
def api_man_get_sign_in_count(man):
    """
    获取派件系人员今日签到次数.
    :param man_id: 人员id
    :return: 5
    """
    url = urls['man_get_what'].format(what='sign_in_count')
    resp = requests.get(url, params=dict(man_id=man['id']), timeout=TIMEOUT)
    return process_bl_response(resp)


# ===> 工作关系相关&取货点相关: 区域经理端用 <===
@api_with_deliveryman_auth
@get('/deliveryman/get/pickup_list')
def api_man_get_pickup_list(man):
    url = urls['man_get_what'].format(what='pickup_list')
    resp = requests.get(url, params=dict(id=man['man_id']), timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_deliveryman_auth
@get('/deliveryman/get/my_code')
def api_man_get_my_code(man):
    url = urls['man_get_what'].format(what='code')
    resp = requests.get(url, params=dict(id=man['man_id']), headers=ctx.request.headers, timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_deliveryman_auth
@get('/deliveryman/get/my_man')
def api_man_get_my_man(man):
    url = urls['man_get_what'].format(what='man_list')
    resp = requests.get(url, params=dict(id=man['man_id']), timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_deliveryman_auth
@get('/deliveryman/outside/search_my_man')
def api_man_outside_search(man):
    kw = Schema({
        'term': schema_unicode_empty,
        Optional("page", default=1): schema_int,
        Optional("count", default=20): schema_int,

        Optional("only", default=['status', 'tel', 'name', 'recommended_by', 'create_time', 'avatar',
                                  'id']): schema_unicode_multi,
        Optional("order_by", default=['name']): schema_unicode_multi,
    }).validate(ctx.request.input())
    term = kw.pop('term')
    # 不传查询条件的话,啥都不返回
    if not term:
        return []
    # 否则,找我符合查询条件的小弟
    query = kw
    query.update({
        "my_manager.id": man['man_id'],
        "$or": [
            {"tel": {"$regex": ".*%s.*" % term}},
            {"name": {"$regex": ".*%s.*" % term}}
        ]
    })

    url = urls['man_complex_query']
    resp = requests.post(url, json=query, timeout=TIMEOUT)
    d = resp.json()
    if not d:
        d = []
    if isinstance(d, dict):
        d = [d]
    ctx.response.set_header("X-Resource-Count".encode('utf-8'), resp.headers.get('X-Resource-Count', '0'))
    return d


@api_with_deliveryman_auth
@post('/deliveryman/working_relation/del_man')
def api_man_working_relation_del_man(man):
    kw = ctx.request.input()
    url = urls['man_del_man']
    resp = requests.post(url, json=dict(manager_id=man['man_id'], man_id=kw.my_man_id), timeout=TIMEOUT)
    return process_bl_response(resp)


# ===> 工作关系相关: 派件员小弟用 <===
@api_with_deliveryman_auth
@post('/deliveryman/working_relation/bind_manager')
def api_man_working_relation_bind_manager(man):
    kw = ctx.request.input()
    url = urls['man_bind_manager']
    resp = requests.post(url, json=dict(code=kw.code, man_id=man['man_id']), timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_deliveryman_auth
@get('/deliveryman/working_relation/apply_unbind_manager')
def api_man_working_relation_apply_unbind_manager(man):
    url = urls['man_apply_unbind_manager']
    resp = requests.get(url, params=dict(man_id=man['man_id']), timeout=TIMEOUT)
    return process_bl_response(resp)


# ===> (对内)后台提现列表,财务支付,财务拒绝; 派件员基本信息查询/操作相关; TODO: 加入后台人员验证 <===
@api
@get('/deliveryman/outsource/finance')
def api_outsource_get_finance_pending():
    """
    @api {get} /deliveryman/outsource/finance [派件员]提现申请列表
    @apiDescription 财务后台查询派件员提现列表.
    @apiName api_outsource_get_finance_pending
    @apiGroup fe_deliveryman

    @apiParam (请求参数) {int} [page] 2. 表示第二页, 从1开始. [1:2147483648), 分页查. 不填表示取所有.
    @apiParam (请求参数) {int} [count] 50. 表示每页50条, 从1开始. [1:2000), 分页查. 不填表示取所有.

    @apiParamExample {str} 请求示例:
        GET /deliveryman/outsource/finance
    @apiSuccessExample {json} 成功示例:
    HTTP/1.1 200 OK
    {
        "content": [
            {
                "type": "DECLINE",
                "transact_num": "20160127117764",
                "tel": "15901739717",
                "account_id": "支付宝id",
                "account_name": "测试艾利斯"
                "cash": 47,
                "create_time": "2016-01-27T14:43:47",
                "remark": "",
                "man_id": "123421rsfhsih" // 派件员ID,
                "can_cash": 999 // 当前可提现的总金额
            },
            ...
        ],
        "error_code": 0,
        "message": ""
    }
    @apiSuccess (返回值) {str} status `APPLY_WITHDRAW`申请中/`PAID`已打款/`DECLINE`财务扣款
    """
    url = urls['flow']
    body = {
        "filter_col": ["type", "transact_num", "tel", "account_id", "account_name",
                       "cash", "create_time", "remark",
                       "man_id"],  # 比原来多返回了一个man_id,用于下面过滤提现申请与flow_statistics的关系
        "query":
            {
                "op": "AND",
                "exprs": [
                    {"type": {"in": ["APPLY_WITHDRAW", "PAID", "DECLINE"]}}
                ]
            },
        "order_by": "type,create_time"
    }
    resp = requests.post(url, json=body, params=ctx.request.input(), timeout=TIMEOUT)
    refund_apply_list = process_bl_response(resp)

    # 加入set_header('X-Resource-Count', count)
    body_to_query_x_res_count = {
        "filter_col": ["count(*)"],
        "query": {
            "op": "AND",
            "exprs": [
                {"type": {"in": ["APPLY_WITHDRAW", "PAID", "DECLINE"]}}
            ]
        },
    }
    resp_xrc = requests.post(url, json=body_to_query_x_res_count, timeout=TIMEOUT)
    x_resource_count = resp_xrc.json()[0]
    ctx.response.set_header("X-Resource-Count".encode('utf-8'), x_resource_count)

    # 给每笔提现申请加一个剩余可提现金额
    man_id_list = [i["man_id"] for i in resp.json()]  # 获取此次需要拿到can_cash的man_id列表
    url_to_get_flow_stats = urls["flow_statistics"]
    body_to_get_flow_can_cash = {  # 查到每个man_id目前的can_cash
        "filter_col": ["man_id", "can_cash"],
        "query": {
            "op": "AND",
            "exprs": [
                {"man_id": {"in": man_id_list}},
            ]
        }
    }
    resp_from_flow_stats = requests.post(url_to_get_flow_stats, json=body_to_get_flow_can_cash, timeout=TIMEOUT)
    flow_stats_man_id_dict = {i["man_id"]: i["can_cash"] for i in resp_from_flow_stats.json()}  # 组成man_id: can_cash字典
    json_to_resp = []
    for i in refund_apply_list:
        i.update({  # 塞进flow的数据结构
            "can_cash": flow_stats_man_id_dict.get(i["man_id"], None)
        })
        json_to_resp.append(i)
    return {
        "content": json_to_resp
    }


@api
@get("/deliveryman/outsource/flow_history")
def api_get_flow_history():
    """
    @api {GET} /deliveryman/outsource/flow_history [派件员]个人提现历史
    @apiDescription 在提现申请列表里查看的提现历史
    @apiName api_get_flow_history
    @apiGroup fe_deliveryman

    @apiParam (url parameter) {string} man_id 人ID

    @apiSuccessExample {str} 成功示例:
        HTTP/1.1 200 OK
        [
            {
                "transact_bum": "交易编号",
                "cash": 123 // 本次提现金额,
                "account_id": "123@qq.com" // 到账账户
                "type": "PAID" // 状态,
                "operator_id": "007" // 操作人ID,
                "create_time": "申请时间"
                "update_time": "操作时间"
            }, ...
        ]

    @apiError (错误码) 401 Token错误
    @apiError (错误码) 400 提现超额或其他逻辑错误.
    """
    man_id = ctx.request.input()["man_id"]
    url = urls['flow']
    body = {
        "filter_col": ["type", "transact_num", "account_id", "cash", "create_time", "update_time", "operator_id"],
        "query":
            {
                "op": "AND",
                "exprs": [
                    {"type": {"in": ["APPLY_WITHDRAW", "PAID", "DECLINE"]}},
                    {"man_id": {"=": man_id}}
                ]
            },
        "order_by": "create_time"
    }
    # todo 加入set_header('X-Resource-Count', count)
    resp = requests.post(url, json=body, timeout=TIMEOUT)
    return process_bl_response(resp)


@api
@post('/deliveryman/outsource/paid')
def api_outsource_paid():
    """
    @api {post} /deliveryman/outsource/paid [派件员]财务已打款
    @apiDescription 财务线下操作转账成功后在后台操作对对应提现申请点击已打款.
    @apiName api_outsource_paid
    @apiGroup fe_deliveryman
    @apiParamExample {json} 请求示例:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/outsource/paid
        Request Method: POST
        Request Payload:
        {
            "tel": "001notexist",
            "transact_num": "20160121144471",
            "cash": 500,
            "operator_id": "7708369"
        }
    @apiSuccessExample {str} 成功示例:
        HTTP/1.1 200 OK
        "20160122945469"
    @apiSuccess (OK 200) {str} transact_num 提交成功的申请交易号
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
            "message": "You are not allowed to apply for cash over [50] yuan."
        }
    @apiError (错误码) 401 Token错误
    @apiError (错误码) 400 提现超额或其他逻辑错误.
    """
    url = urls["flow_paid"]
    body = ctx.request.input()
    body['operator_id'] = '007'
    resp = requests.post(url, json=body, timeout=TIMEOUT)
    return process_bl_response(resp)


@api
@post('/deliveryman/outsource/decline')
def api_outsource_decline():
    """
    @apiIgnore
    @api {post} /deliveryman/outsource/decline [派件员]财务已扣款
    @apiDescription 财务在后台操作对对应提现申请点击拒绝该笔提现申请（一旦拒绝,该笔金额将永久被扣除,无法再次提现）.
    @apiName api_outsource_decline
    @apiGroup fe_deliveryman
    @apiParamExample {json} 请求示例:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/outsource/decline
        Request Method: POST
        Request Payload:
        {
            "transact_num": "20160310hqf9vS",
            "cash": 4.1,
            "operator_id": "007",
            "remark": "罚款"
        }
    @apiSuccessExample {str} 成功示例:
        HTTP/1.1 200 OK
        "20160122945469"
    @apiSuccess (返回值) {str} transact_num 提交成功的申请交易号
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
            "message": "Cash flow for transact_num=[20160121189599] has been VALIDATED."
        }
    @apiError (错误码) 401 Token错误
    @apiError (错误码) 400 已操作的交易或其他逻辑错误.
    """
    url = urls["flow_decline"]
    body = ctx.request.input()
    # todo: 添加后台验证
    body['operator_id'] = '007'
    resp = requests.post(url, json=body, timeout=TIMEOUT)
    return process_bl_response(resp)


@api
@post('/deliveryman/:fe_operation')
def api_man_operation(operation):
    """
    @api {post} /deliveryman/:fe_operation [派件员]后台FSM操作
    @apiDescription 上帝操作,拉黑,判定资料通过,判定资料有误,修改资料.
    @apiName api_man_operation
    @apiGroup fe_deliveryman

    @apiParam {str} OPERATION URI中: 限定URI接口操作,可选值: `event_reset`, `event_ban`,
     `event_complete_info`, `event_hr_decide_info_mistaken`, `event_hr_decide_yes`.
    @apiParamExample {json} 判定资料通过:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/event_hr_decide_yes
        Request Method: POST
        Request Payload:
        {
            "man_id": "56c2e7d97f4525452c8fc23c"
        }
    @apiParamExample {json} 判定资料有误:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/event_hr_decide_info_mistaken
        Request Method: POST
        Request Payload:
        {
            "man_id": "56c2e7d97f4525452c8fc23c",
            "remark": "身份证号有误"
        }
    @apiParamExample {json} 修改资料:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/event_complete_info
        Request Method: POST
        Request Payload:
        {
            "man_id": "56c2e7d97f4525452c8fc23c",
            "id_card_num": "123456789012345678",
            "name": "测试1号",
            "avatar": "AF9650D87988D915577E4130422187CE",
            "id_card_back": "AF9650D87988D915577E4130422187CE"
        }
    @apiParamExample {json} 拉黑:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/event_ban
        Request Method: POST
        Request Payload:
        {
            "man_id": "56c2e7d97f4525452c8fc23c",
            "remark": "测试拉黑"
        }
    @apiParamExample {json} 上帝操作:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/event_reset
        Request Method: POST
        Request Payload:
        {
            "man_id": "56c2e7d97f4525452c8fc23c",
            "remark": "测试上帝操作"
        }
    @apiSuccessExample {json} 成功示例:
        HTTP/1.1 200 OK

    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
            "message": "Already added."
        }
    @apiError (错误码) 401 Token错误
    @apiError (错误码) 400 重复添加或其他逻辑错误.
    """
    operation = str(operation).upper().strip()
    if operation in FE_EVENTS:
        url = urls["man_operation"].format(operation=operation)
        kw = ctx.request.input()
        kw['operator_type'] = 'FE'
        resp = requests.post(url, json=kw, timeout=TIMEOUT)
        return process_bl_response(resp)
    else:
        raise ValueError("operation[%s] to be supported~" % operation)


@api
@get("/deliveryman/search")
def api_deliveryman_search():
    """
    @api {get} /deliveryman/search [派件员]搜索
    @apiDescription 按照手机号/名字/状态 搜索派件员
    @apiName api_deliveryman_search
    @apiGroup fe_deliveryman

    @apiParam {string(11)} [term] 派件员手机号(或者一部分手机号)/名字(如有), 如 6202.
    @apiParam {list} [status_list] 派件员状态集合, 如 ["STATUS_INFO_COMPLETED", "STATUS_WORKING"], 省略该参数表示所有状态.
    @apiParamExample {json} 搜索示例:
        Request URL: http://dev.api.mrwind.com:5000/deliveryman/search?status_list=STATUS_INIT&term=80
        Request Method: GET

    @apiSuccessExample {json} 成功示例:
        HTTP/1.1 200 OK
        [
            {
                "status": "STATUS_INIT",
                "tel": "15967196202",
                "create_time": "2016-02-26 07:41:32",
                "accounts": [
                    {
                        "id": "15967196202",
                        "name": "王连"
                    }
                ],
                "job_description": "outsource",
                "familiars": [],
                "man_id": "56cf912ceed09372906da06a"
            }, ...
        ]
    """
    url = urls["man_complex_query"]
    kw = Schema({
        Optional(object): object,
        Optional('status_list', default=[]): schema_unicode_multi,
        Optional('create_time_s', default=None): schema_unicode,
        Optional('create_time_e', default=None): schema_unicode,

        Optional("page", default=1): schema_int,
        Optional("count", default=20): schema_int,

        Optional("only", default=[]): schema_unicode_multi,
        Optional("order_by", default=['name']): schema_unicode_multi,
    }).validate(ctx.request.input())

    status_list = kw['status_list']
    create_time_s = kw['create_time_s']
    create_time_e = kw['create_time_e']
    term = kw.get('term')
    man_id = kw.get('man_id')
    # 如果按照id查详情
    if man_id:
        query = {"_id": man_id}
    # 如果传入了搜索条件,且搜索条件不为空.
    elif term:
        query = {
            "$or": [
                {"tel": {"$regex": ".*%s.*" % term}},
                {"name": {"$regex": ".*%s.*" % term}}
            ]
        }
        if status_list:
            query["status"] = {"$in": status_list}
    # 否则认为是过滤
    else:
        query = {}
        if status_list:
            query["status"] = {"$in": status_list}
        if create_time_s and create_time_e:
            create_time_s = utc_8_to_utc(create_time_s, ret='datetime')
            create_time_e = utc_8_to_utc(create_time_e, ret='datetime')
            query["create_time"] = {"$gte": create_time_s, "$lte": create_time_e}
        query = dict(query=pickle.dumps(query))

    # 统一加上附加参数
    query['page'] = kw['page']
    query['count'] = kw['count']
    query['only'] = kw['only']
    query['order_by'] = kw['order_by']

    resp = requests.post(url, json=query, timeout=TIMEOUT)
    d = resp.json()
    if not d:
        d = []
    if isinstance(d, dict):
        d = [d]
    ctx.response.set_header("X-Resource-Count".encode('utf-8'), resp.headers.get('X-Resource-Count', '0'))
    return d


# ===> (对外)商户基本信息相关: 验证码,注册,登录,修改资料 <===
@api
@get('/shop/sms_code')
def api_shop_sms_code():
    """
    @api {get} /shop/sms_code [商户]获取验证码
    @apiName api_shop_sms_code
    @apiGroup fe_shop

    @apiParam {string(11)} [tel] 用于接受验证码的手机号, 如 13245678901.

    @apiParamExample {json} 请求url/param示例:
    Request Method: GET
    Request URL: http://dev.api.mrwind.com:5000/shop/sms_code?tel=13245678901
    @apiSuccessExample {json} 获取验证码成功示例:
        HTTP/1.1 200 OK
        {}
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
          "message": "error msg."
        }
    """
    url = urls["shop_sms"]
    param = ctx.request.input()
    # 如果是QA,不发验证码.
    if not DEBUG and param.tel in list(QA.keys()):
        raise ValueError("检测到%s尝试获取PROD验证码.请用【13245678901:111111】登录." % QA[param.tel])
    resp = requests.get(url, params=param, timeout=TIMEOUT)
    process_bl_response(resp)


@api
@post('/shop/register')
def api_shop_register():
    """
    @api {post} /shop/register [客户]注册
    @apiName api_shop_register
    @apiGroup common_shop

    @apiParam {string(11)} tel 客户注册手机号, 如 13245678902.
    @apiParam {string(6)} sms_code 验证码, 如123456.
    @apiParam {string(32)} password 密码md5哈希.
    @apiParam {string(64)} name 客户名称.
    @apiParam {json} loc 客户地址.
    @apiParam {string(32)} [loc.city] 客户(发货)地址所在城市.
    @apiParam {string(128)} loc.address 客户(发货)地址.
    @apiParam {float(10)} loc.longitude 客户(发货)地址经度.
    @apiParam {float(10)} loc.latitude 客户(发货)地址纬度.
    @apiParam {json} recommended_by 推荐人.
    @apiParam {string(11)} [recommended_by.tel] 推荐人手机号.

    @apiParamExample {json} 请求示例:
    Request Method: POST
    Request URL: http://dev.api.mrwind.com:5000/shop/register
    Request Body:
        {
            "tel": "13245678912",
            "sms_code":"123456",
            "password": "e10adc3949ba59abbe56e057f20f883e",

            "name": "测试乌冬",

            "loc": {
                "city": "杭州市",
                "address": "白银市景泰县天府渔庄",
                "latitude": 30.177548,
                "longitude": 120.300298
            },

            "recommended_by": {
                "tel": "13245678901"
            }
        }
    @apiSuccessExample {json} 成功返回更新后商户详情示例:
        HTTP/1.1 200 OK
        {
            "status": "STATUS_VALID",
            "shop_id": "5755204f421aa90f5a728b7d",
            "name": "测试乌冬",
            "tel": "13245678912",
            "loc": {
                "city": "杭州市",
                "address": "白银市景泰县天府渔庄",
                "latitude": 30.177548,
                "longitude": 120.300298
            },
            "recommended_by": {
                "tel": "13245678901",
                "time": "2016-06-06T15:03:43"
            },
            "contact": {
                "tel": "13245678912",
                "name": "测试乌冬"
            },
            "create_time": "2016-06-06T15:03:43",
            "requirement": null,
            "fee": null,
            "token": "b8548c35163632c496940ec2b12a8b78"
        }
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
            "message": "error message"
        }
    """
    kw = Schema({
        'tel': schema_unicode,
        'sms_code': schema_unicode,
        'password': schema_unicode,

        Optional('name'): schema_unicode,

        Optional('contact', default={'name': '', 'tel': ''}): {
            Optional('name', default=''): schema_unicode_empty,
            Optional('tel', default=''): schema_unicode_empty
        },
        # 'requirement': {
        #     "forecast_orders": schema_int,
        #     "cargo_type": schema_unicode,
        #     "average_size": schema_unicode,
        #     "time_limit": schema_unicode,
        #     Optional("remark"): schema_unicode_empty
        # },
        Optional("loc"): {
            "address": schema_unicode,
            "longitude": schema_float,
            "latitude": schema_float,
            Optional("city", default='杭州市'): schema_unicode,
            Optional(object): object
        },
        Optional('recommended_by'): {
            Optional('tel', default=''): schema_unicode_empty
        },
    }).validate(ctx.request.input())
    # 默认联系人方式设置为注册电话
    if not kw['contact']['tel']:
        kw['contact']['tel'] = kw['tel']
        kw['contact']['name'] = kw.get('name', '')
    url = urls['shop_operation'].format(operation='register')
    resp = requests.post(url, json=kw, timeout=TIMEOUT)
    return process_bl_response(resp)


@api
@get('/shop/login')
def api_shop_login():
    """
    @api {get} /shop/login [商户]登录
    @apiName api_shop_login
    @apiGroup fe_shop

    @apiParam {string(11)} tel 商户注册手机号, 如 13245678901.
    @apiParam {string(32)} password 密码md5哈希.

    @apiParamExample {json} 请求示例:
    Request Method: GET
    Request URL: http://dev.api.mrwind.com:5000/shop/login?tel=15988163877&password=bc65354d3a5c1f77a585
    @apiSuccessExample {json} 成功示例:
        HTTP/1.1 200 OK
        {
            "status": "STATUS_INIT",
            "loc": {
                "province": "浙江省",
                "city": "杭州市",
                "district": "滨江区",
                "province_code": 330000000000,
                "address": "浙江省杭州市滨江区秋溢路228号江虹国际创意园3A102",
                "street_code": 0,
                "longitude": 120.208003,
                "street": "秋溢路",
                "district_code": 330108000000,
                "latitude": 30.19606,
                "city_code": 330100000000
            },
            "tel": "15988163877",
            "name": "F2鲜果",
            "token": "86dcb90a71377813f35322a4548a0d13",
            "shop_id": "56c2d708a785c90ab0014d00",
            "create_time": "2015-02-28 11:25:39"
        }
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValidationError
        {
            "message": "error message"
        }
    """
    url = urls["shop_login"]
    resp = requests.get(url, params=ctx.request.input(), timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_shop_auth
@post('/shop/outside/:outside_operation')
def api_shop_out_operation(operation, shop_id):
    operation = str(operation).upper().strip()
    kw = ctx.request.input()
    # 对完善资料额外做参数校验
    if operation == OUTSIDE_EVENTS.EVENT_COMPLETE_INFO:
        kw = Schema({
            'name': schema_unicode,
            'contact': {
                'name': schema_unicode,
                'tel': schema_unicode
            },
            'requirement': {
                "forecast_orders": schema_int,
                "cargo_type": schema_unicode,
                "average_size": schema_unicode,
                "time_limit": schema_unicode,
                Optional("remark"): schema_unicode_empty
            },
            "loc": {
                "address": schema_unicode,
                "longitude": schema_float,
                "latitude": schema_float,
                Optional(object): object
            },
            Optional('recommended_by'): {
                'tel': schema_unicode_empty
            },
        }).validate(kw)
    # 统一处理
    if operation in OUTSIDE_EVENTS:
        url = urls['shop_operation'].format(operation=operation)
        kw['operator_type'] = 'OUTSIDE'
        kw['shop_id'] = shop_id
        resp = requests.post(url, json=kw, timeout=TIMEOUT)
        return process_bl_response(resp)
    else:
        logging.warn("[OUTSIDE]operation[%s] to be supported~" % operation)
        raise ValueError('操作[%s]尚未支持.' % operation)


@api
@get('/shop/search')
def api_shop_search():
    url = urls['shop_complex_query']
    kw = ctx.request.input()
    status_list = literal_eval(kw.get("status_list", "[]"))
    create_time_s = kw.get('create_time_s')
    create_time_e = kw.get('create_time_e')
    term = kw.get('term')

    if term:
        query = {
            "$or": [
                {"tel": {"$regex": ".*%s.*" % term}},
                {"name": {"$regex": ".*%s.*" % term}}
            ]
        }
    else:
        query = {}
        if status_list:
            query["status"] = {"$in": status_list}
        if create_time_s and create_time_e:
            create_time_s = utc_8_to_utc(create_time_s, ret='datetime')
            create_time_e = utc_8_to_utc(create_time_e, ret='datetime')
            query["create_time"] = {"$gte": create_time_s, "$lte": create_time_e}
    query = dict(query=pickle.dumps(query))
    if 'page' in kw:
        query['page'] = kw['page']
    if 'count' in kw:
        query['count'] = kw['count']
    resp = requests.post(url, json=query, timeout=TIMEOUT)
    d = resp.json()
    if not d:
        d = []
    elif isinstance(d, dict):
        d = [d]
    ctx.response.set_header("X-Resource-Count".encode('utf-8'), resp.headers.get('X-Resource-Count', '0'))
    return d


@api
@post('/shop/inside/:fe_inside_operation')
def api_shop_in_operation(operation):
    operation = str(operation).upper().strip()
    kw = ctx.request.input()
    # 对修改定价特殊处理: 1.要求secret key 2.能用tel找商户id 3.设置默认配送费是4.6
    if operation == FE_INSIDE_EVENTS.EVENT_ALTER_INFO:
        if kw.secret_key != 'UE#93j~tBac3$sC':
            ctx.response.status = '403 Forbidden'
            return
    # 事件具体处理
    if operation in FE_INSIDE_EVENTS:
        url = urls['shop_operation'].format(operation=operation)
        kw['operator_type'] = 'FE_INSIDE'
        resp = requests.post(url, json=kw, timeout=TIMEOUT)
        return process_bl_response(resp)
    else:
        raise ValueError("[FE_INSIDE]operation[%s] to be supported~" % operation)


# ===> 商户金钱相关:充值 <===
@api_with_shop_auth
@post('/shop/top_up')
def api_shop_web_top_up(shop_id):
    """
    @api {post} /shop/top_up [商户]充值-PC端支付宝网页
    @apiName api_shop_web_top_up
    @apiGroup fe_shop

    @apiUse AuthHeader
    @apiParam {decimal} cash 充值金额（元）,精确到小数点后2位, ROUND_DOWN.

    @apiParamExample {json} 请求示例:
    Request Method: POST
    Request URL: http://dev.api.mrwind.com:5000/shop/top_up
    Request Body:
        {
            "cash": 0.01
        }
    @apiSuccessExample {json} 充值跳转链接成功生成示例:
        HTTP/1.1 200 OK
        {
            "url": "https://mapi.alipay.com/gateway.do?seller_email=abcx%40123feng.com&seller_id=2088901729140845&total_fee=0.01&service=create_direct_pay_by_user&_input_charset=utf-8&sign=f81aeee8397e8924001a50559c588cc4&out_trade_no=20160301227319&payment_type=1&notify_url=http%3A%2F%2Fdev.api.mrwind.com%3A5000%2Fshop%2Fweb_top_up_callback&sign_type=MD5&partner=2088901729140845&subject=charge",
            "transact_num": "20160301227319"
        }
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValidationError
        {
            "message": "error message"
        }
    """
    params = ctx.request.input()
    params['shop_id'] = shop_id

    url = urls["shop_web_top_up"]
    if 'cash' not in params:
        raise ValueError("Should provide me with param [cash] in body.")
    cash = round(decimal.Decimal(params.cash), 2)
    if cash <= 0.0:
        raise ValueError("Cash[%s] should be at least [0.01]." % params.cash)
    params.cash = cash
    resp = requests.post(url, json=params, timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_shop_auth
@post('/shop/app_top_up')
def api_shop_app_top_up(shop_id):
    params = ctx.request.input()
    params['shop_id'] = shop_id

    url = urls['shop_app_top_up']
    if 'cash' not in params:
        raise ValueError('Should provide me with param [cash] in body.')
    cash = round(decimal.Decimal(params.cash), 2)
    if cash <= 0.0:
        raise ValueError('Cash[%s] should be at lease [0.01].' % params.cash)
    params.cash = cash
    resp = requests.post(url, json=params, timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_shop_auth
@post('/shop/wap_top_up')
def api_shop_wap_top_up(shop_id):
    # 输入params: cash
    params = ctx.request.input()
    params.shop_id = shop_id

    url = urls['shop_wap_top_up']
    if 'cash' not in params:
        raise ValueError("Should provide me with param [cash] in body.")
    cash = round(decimal.Decimal(params.cash), 2)
    if cash <= 0.0:
        raise ValueError("Cash[%s] should be at least [0.01]." % params.cash)
    params.cash = cash
    resp = requests.post(url, json=params, timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_shop_auth
@get('/shop/h5/js_sdk_signature')
def api_shop_h5_get_js_sdk_signature(shop_id):
    url = urls['js_sdk_signature']
    resp = requests.get(url, params=ctx.request.input(), timeout=TIMEOUT)
    return process_bl_response(resp)


@api_with_shop_auth
@post('/shop/h5/wx_top_up')
def api_shop_h5_wx_top_up(shop_id):
    # 输入params: cash
    params = ctx.request.input()
    params.shop_id = shop_id

    url = urls['shop_h5_wx_top_up']
    if 'cash' not in params:
        raise ValueError("Should provide me with param [cash] in body.")
    cash = round(decimal.Decimal(params.cash), 2)
    if cash <= 0.0:
        raise ValueError("Cash[%s] should be at least [0.01]." % params.cash)
    params.cash = cash
    resp = requests.post(url, json=params, timeout=3)
    return process_bl_response(resp)


@api
@post('/shop/web_top_up_callback')
def api_shop_web_top_up_cb():
    """
    PC网页端和APP客户端共用的回调.
    :return:
    """
    url = urls["shop_web_app_top_up_callback"]
    resp = requests.post(url, json=ctx.request.input(), timeout=TIMEOUT)
    return process_alipay_top_up_resp_obj(resp)


@api
@post('/shop/wap_top_up_callback')
def api_shop_wap_top_up_cb():
    url = urls['shop_wap_top_up_callback']
    resp = requests.post(url, json=ctx.request.input(), timeout=TIMEOUT)
    return process_alipay_top_up_resp_obj(resp)


@api
@post('/shop/wx_top_up_callback')
def api_shop_wx_top_up_callback():
    url = urls['shop_h5_wx_top_up_callback']
    body = ctx.request.get_body()
    # logging.info(body)
    resp_obj = requests.post(url, data=body, headers=ctx.request.headers, timeout=3)
    resp = process_wxpay_resp_obj(resp_obj)
    return resp['ret']


@api
@post('/shop/wx_pay_callback')
def api_shop_native_wx_pay_callback():
    body = ctx.request.get_body()
    # logging.info(body)
    # 1. 改flow_top_up,flow,flow_statistics;(如果是第一次成功的通知)
    url = urls['shop_native_wx_pay_callback']
    flow_resp_obj = requests.post(url, data=body, headers=ctx.request.headers, timeout=0.7)
    # 判断返回msg: 只有是FlowLogic.MSGS.notify_first_success才需要去查transact_num对应的number_list,cash并且批量修改订单状态.
    resp = process_wxpay_resp_obj(flow_resp_obj)
    logging.info(resp)
    msg = resp['msg']
    if msg == 'notify_first_success':
        logging.info(ctx.response.headers)
        """注意: 回调的部分, 要根据transact_num
        2. 改aeolus.call.transact_list的trade_no;
        3. 改aeolus.express对应于number_list里面的运单的状态们.
        """
        url = urls['pay_call_back_notify_first_success']
        # resp应该形如Schema({
        #     'ret': schema_unicode,  # generate_xml({'return_code': 'SUCCESS'})
        #     'msg': schema_unicode,  # FlowLogic.MSGS: 现在只处理notify_first_success
        #     'transact_num': schema_unicode,
        #     'trade_no': schema_unicode
        # })
        call_expr_resp_obj = requests.patch(url, data=json.dumps(resp), headers={'Content-Type': 'application/json'},
                                            timeout=TIMEOUT)
        process_bl_response(call_expr_resp_obj)
    return resp['ret']


@api
@post('/shop/alipay_callback')
def api_shop_alipay_callback():
    body = ctx.request.get_body()
    logging.info(repr(body))

    # 1. 改flow_top_up,flow,flow_statistics;(如果是第一次成功的通知)
    url = urls['shop_native_alipay_callback']
    flow_resp_obj = requests.post(url, data=body, headers=ctx.request.headers, timeout=0.7)
    # 判断返回msg: 只有是FlowLogic.MSGS.notify_first_success才需要去查transact_num对应的number_list,cash并且批量修改订单状态.
    resp = process_bl_response(flow_resp_obj)
    logging.info(resp)
    msg = resp['msg']
    if msg == 'notify_first_success':
        logging.info(ctx.response.headers)
        """注意: 回调的部分, 要根据transact_num
        2. 改aeolus.call.transact_list的trade_no;
        3. 改aeolus.express对应于number_list里面的运单的状态们.
        """
        url = urls['pay_call_back_notify_first_success']
        # resp应该形如Schema({
        #     'ret': schema_unicode,  # 'success'
        #     'msg': schema_unicode,  # FlowLogic.MSGS: 现在只处理notify_first_success
        #     'transact_num': schema_unicode,
        #     'trade_no': schema_unicode
        # })
        call_expr_resp_obj = requests.patch(url, data=json.dumps(resp), headers={'Content-Type': 'application/json'},
                                            timeout=TIMEOUT)
        process_bl_response(call_expr_resp_obj)
    return resp['ret']


@api_with_deliveryman_auth
@get('/deliveryman/check_shop_transact')
def api_shop_check_transact(man):
    params = Schema({
        'transact_num': schema_unicode
    }).validate(ctx.request.input())

    url = urls['check_shop_transact']
    resp_obj = requests.get(url, params=params, timeout=TIMEOUT)
    return process_bl_response(resp_obj)


@api_with_shop_auth
@get('/shop/balance')
def api_shop_balance(shop_id):
    """
    @api {get} /shop/balance [商户]余额
    @apiName api_shop_balance
    @apiGroup fe_shop

    @apiUse AuthHeader

    @apiParamExample {json} 请求示例:
    Request Method: GET
    Request URL: http://dev.api.mrwind.com:5000/shop/balance
    @apiSuccessExample {string} 成功示例:
        HTTP/1.1 200 OK
        0.33
    @apiErrorExample {json} 失败示例:
        HTTP 400 ValueError:
        {
            "message": "error message"
        }
    """
    params = ctx.request.input()
    params['shop_id'] = shop_id

    url = urls["shop_balance"]
    query = {
        "filter_col": ["balance"],
        "query":
            {
                "op": "AND",
                "exprs": [
                    {"shop_id": {"=": shop_id}},
                ]
            }
    }
    resp = requests.post(url, json=query, timeout=TIMEOUT)
    ret = process_bl_response(resp)
    if len(ret) == 1:
        return ret[0]
    else:
        return 0.0


@api_with_shop_auth
@get('/shop/expense')
def api_shop_expense(shop_id):
    """
    @api {get} /shop/expense [商户]消费
    @apiName api_shop_expense
    @apiGroup fe_shop

    @apiUse AuthHeader

    @apiParamExample {json} 请求示例:
    Request Method: GET
    Request URL: http://dev.api.mrwind.com:5000/shop/expense
    @apiSuccessExample {string} 成功示例:
        HTTP/1.1 200 OK
        0.01
    @apiErrorExample {json} 失败示例:
        HTTP 400 ValueError:
        {
            "message": "error message"
        }
    """
    params = ctx.request.input()
    params['shop_id'] = shop_id

    url = urls["shop_expense"]
    query = {
        "filter_col": ["expense"],
        "query":
            {
                "op": "AND",
                "exprs": [
                    {"shop_id": {"=": shop_id}},
                ]
            }
    }
    resp = requests.post(url, json=query, timeout=TIMEOUT)
    ret = process_bl_response(resp)
    if len(ret) == 1:
        return ret[0]
    else:
        return 0.0


@api_with_shop_auth
@get('/shop/flow')
def api_shop_flow(shop_id):
    """
    拿这个商户的消费明细
    :param shop_id:
    :return:
    """
    kw = ctx.request.input()
    url = urls['shop_flow']
    body = {
        "filter_col": ["type", "create_time", "cash", "balance"],
        "query":
            {
                "op": "AND",
                "exprs": [
                    {"shop_id": {"=": shop_id}},
                ]
            },
        "order_by": "create_time desc",
        "page": kw.get('page', 1),
        "count": kw.get('count', 20)
    }
    resp = requests.post(url, json=body, timeout=TIMEOUT)
    ctx.response.set_header("X-Resource-Count".encode('utf-8'), resp.headers.get('X-Resource-Count', '0'))
    return process_bl_response(resp)
