# coding:utf-8
from __future__ import unicode_literals

import decimal
import hashlib
import logging
import pickle
import random

import shortuuid
from bson import ObjectId
from model_logics.fsm import ShopFSM
from model_logics.logics import ShopLogic, TopUpLogic, FlowLogic, FlowStatisticsLogic
from model_logics.models import Shop, TRANSACT_TYPE
from schema import Schema, Optional
from tools_lib.java_account import SyncAccount
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.common_util.third_party.sms_api import check_tel, send_code, SEND_SMS_SUCCESS
from tools_lib.gedis.core_redis_key import (key_shop_token, key_no_password, key_sms_code, key_access_token,
                                            key_jsapi_ticket)
from tools_lib.gedis.gedis import Redis
from tools_lib.pay.alipay_config import WEB_NOTIFY_URL
from tools_lib.pay.alipay_qrcode import alipay_generate_prepay_native, alipay_native_callback
from tools_lib.pay.alipay_wap import (create_wap_trade, wap_trade_notice_handler,
                                      gen_wap_transfer_link, wap_transfer_notice_handler)
from tools_lib.pay.alipay_web import create_web_trade, web_trade_notice_handler
from tools_lib.pay.wxpay import (wx_generate_prepay_jsapi, wx_callback, generate_xml, get_access_token,
                                 get_jsapi_ticket, get_js_sdk_signature, wx_generate_prepay_native)
from tools_lib.transwarp.complex_query_parser import complex_query, parse_page_count
from tools_lib.transwarp.escape import schema_unicode, schema_unicode_empty, schema_float, schema_float_2, schema_int
from tools_lib.transwarp.tz import utc_8_now, utc_8_day
from tools_lib.transwarp.web import Dict, safe_str
from tools_lib.transwarp.web import ctx, post, api, get
from tools_lib.windchat import account, conf
from tornado.httpclient import HTTPClient

# === 缓存 ===
redis_client = Redis()
# === 商户基本信息相关 ===
OPERATIONS = Dict(**{x: x for x in ("REGISTER", "CHANGE_PASSWORD", "CHANGE_TEL")})


@api
@get('/shop/sms_code')
def api_shop_sms_code():
    params = ctx.request.input()
    tel = str(params.get("tel", "")).strip()
    if not tel:
        raise ValueError("Should provide me with [tel] in params.")
    elif not check_tel(tel):
        raise ValueError("[tel] should be of length 11 and starts with digit 1.")

    sms_code = random.randrange(100000, 999999)
    # 同步发短信: 确保发送成功再改redis.
    send = send_code(tel, sms_code)
    if send == SEND_SMS_SUCCESS:
        sms_key = key_sms_code.format(tel=tel)
        # 插入验证码到redis中, 10分钟有效期: get sms:code:13245678901 => 123456
        redis_client.setex(sms_key, sms_code, 600)
        return sms_code
    else:
        raise ValueError("运营商发送验证码失败,请重试.")


@api
@get('/shop/login')
def api_shop_login():
    """
    @api {get} /shop/login?shop_id=&password= [商户]登录
    @apiDescription 风先生商户登录成功则返回token,失败则报错.
    @apiName api_shop_login
    @apiGroup shop

    @apiParam {string(11)} [shop_id] 商户工号, 如 7748657.
    @apiParam {string(11)} [tel] 商户手机号, 如 150687929321.
    @apiParam {string(32)} password 商户密码hash(如果是id+密码登录), 验证码(如果是手机号+验证码登录).

    @apiParamExample {json} 请求url示例:
          /shop/login?shop_id=17066&password=0192023a7bbd73250516f069df18b500
    OR    /shop/login?tel=150687929321&password=123456
    @apiSuccessExample {json} 手机号验证码登录成功示例:
        HTTP/1.1 200 OK
        {
          "tel": "150687929321",
          "token": "36dc92e290f334aaa96466d3ee9b9efa"
        }
    @apiSuccessExample {json} 工号密码登录成功示例:
        HTTP/1.1 200 OK
        {
          "shop_id": "17066",
          "token": "36dc92e290f334aaa96466d3ee9b9efa"
        }
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
          "message": "No such shop=[150687929321]."
        }
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
          "message": "Password validation for [17066]=[012023a7bbd73250516f069df18b500] failed."
        }
    """

    def set_token(inner_who):
        token = hashlib.md5('%s%s' % (inner_who, utc_8_now())).hexdigest()
        key = key_shop_token.format(content=token)
        # 插入token到redis中, 30天有效期: get token:fe11ad907e2fa779ed2f363ef589d3f9 => 7740959
        redis_client.setex(key, inner_who, 30 * 24 * 3600)
        return token

    params = ctx.request.input()
    shop_id = str(params.get("id", "")).strip()
    tel = str(params.get("tel", "")).strip()
    password_or_sms_code = str(params.get('password', '')).strip()

    # ==> 首先检查是不是免密码[优先级为: 免密码>手机]
    who = shop_id if shop_id else tel if tel else None
    if not who:
        raise ValueError("Expect either [shop_id] or [tel] in params%s." % params)
    elif not password_or_sms_code:
        raise ValueError("Expect [password] in params%s." % params)
    # 存放: 免密码名单和token(30天)
    # 登录成功: smembers no_password => set(13245678901,...); sismember(key_login, tel)
    elif redis_client.sismember(key_no_password, who):
        if tel:
            shop = Shop.objects(tel=tel).first()
            content = set_token(str(shop.pk))
            s_packed = ShopLogic.pack_shop(shop)
            s_packed.update(dict(token=content))
            return s_packed

    # ==> 商户登录: 商户owner手机号+密码
    shop = None
    if shop_id:
        shop = Shop.objects(id=shop_id).first()
    elif tel:
        shop = Shop.objects(tel=tel).first()
    password_in_db = str(shop.password).strip() if shop else None
    # 如果此人不存在,直接报错
    if not password_in_db:
        logging.info("No such shop=[%s]." % who)
        raise ValueError("商户不存在,请注册后登录.")
    # 登录成功: 密码与数据库中值匹配
    if password_or_sms_code == password_in_db:
        content = set_token(str(shop.pk))
        s_packed = ShopLogic.pack_shop(shop)
        s_packed.update(dict(token=content))
        return s_packed
    # 登录失败
    else:
        logging.info(
            "Password validation for [%s]=[%s] failed, expected [%s]." % (who, password_or_sms_code, password_in_db))
        raise ValueError("用户名或密码错误.")


@api
@get('/shop/token')
def api_get_shop_info_from_token():
    # 输入: token <token>
    params = ctx.request.input()
    if 'token' not in params:
        logging.warning("You are calling /shop/token without [token] key in params%s." % params)
    token = params.token.split()[1]
    key = key_shop_token.format(content=token)
    # 可能值: id
    who = redis_client.get(key)
    if not who:
        ctx.response.status = '401 Unauthorized'
        return None

    elif len(who) == 24:
        s = Shop.objects(id=who).first()
        # 如果该商户没有定价, 取默认定价
        if s.fee and s.fee.get('fh'):
            pass
        else:
            _s = Shop.objects(tel='00000000000').only('fee').first()
            s.fee = _s.fee
        return ShopLogic.pack_shop(s)


@api
@post('/shop/complex_query')
def api_retrieve_shop_info():
    """
    @api {post} /shop/complex_query/:page [商户]基本信息复杂查询
    @apiDescription 查询多条商户详细信息记录(mongodb __raw__).
    @apiName api_retrieve_shop_info
    @apiGroup shop

    @apiParamExample {json} 请求body示例:
        {
            "_id": "56c2d708a785c90ab0014d00"
        }
    """
    kw = ctx.request.input()
    query = {}

    if 'query' in kw:
        query = pickle.loads(kw.query)
    if '_id' in kw:
        query['_id'] = ObjectId(kw['_id'])
    for k in ('tel', 'name'):
        if k in kw:
            query[k] = kw[k]
    page, count = parse_page_count(kw)

    excludes = (str('password'),)
    only = kw.get('only')
    if only:
        shops = Shop.objects(__raw__=query).only(*only).skip((page * count)).limit(count)
    else:
        shops = Shop.objects(__raw__=query).exclude(*excludes).skip((page * count)).limit(count)
    _count = Shop.objects(__raw__=query).count()
    ret = []
    for s in shops:
        s_packed = ShopLogic.pack_shop(s, excludes=excludes, only=only)
        ret.append(s_packed)
    ctx.response.set_header("X-Resource-Count".encode('utf-8'), _count)
    return ret[0] if len(ret) == 1 else ret if len(ret) > 1 else {}


@api
@post('/shop/fsm/:OPERATION')
def api_shop_operation(operation):
    def set_token(inner_who):
        token = hashlib.md5('%s%s' % (inner_who, utc_8_now())).hexdigest()
        key = key_shop_token.format(content=token)
        # 插入token到redis中, 7天有效期: get shop:token:fe11ad907e2fa779ed2f363ef589d3f9 => 7740959
        redis_client.setex(key, inner_who, 7 * 24 * 3600)
        return token

    operation = str(operation).upper().strip()
    kw = ctx.request.input()
    # ==> 商户注册
    if operation == OPERATIONS.REGISTER:
        kw = Schema({
            'tel': schema_unicode,
            'sms_code': schema_unicode,
            'password': schema_unicode,
            Optional('name'): schema_unicode,
            'contact': {
                Optional('name', default=''): schema_unicode_empty,
                Optional('tel', default=''): schema_unicode_empty
            },
            Optional("loc"): {
                "address": schema_unicode,
                "longitude": schema_float,
                "latitude": schema_float,
                Optional(object): object
            },
            Optional('recommended_by'): {
                'tel': schema_unicode_empty
            },
        }).validate(ctx.request.input())
        tel = kw['tel']
        sms_code = kw['sms_code']
        password = kw['password']
        # song.123feng.com/APP注册: 手机号+验证码
        if tel:
            sms_key = key_sms_code.format(tel=tel)
            # 验证成功: 验证码匹配 get sms:code:15901739717 => 123456
            sms_code_in_redis = redis_client.get(sms_key)
            if sms_code_in_redis == sms_code:
                shop = Shop.objects(tel=tel).first()
                if not shop:
                    # 记录商户到mongodb(如无记录): status=STATUS_VALID
                    # 记录商户到mongodb(如无记录): status=STATUS_INFO_YES
                    if 'recommended_by' in kw:
                        kw['recommended_by']['time'] = TimeZone.utc_now()
                    kw_filtered = ShopLogic.filter_shop(kw)
                    shop = Shop(**kw_filtered).save()
                    # ===== 注册风信账户 =====
                    http_client = HTTPClient()
                    http_client.fetch(account.req_create(
                        account_type=conf.ACCOUNT_TYPE_SHOP,
                        account_id=str(shop.pk)
                    ), raise_error=False)
                else:
                    # 允许重复注册, 改一下密码
                    shop.password = password
                    shop.save()
                shop.reload()
                shop_id = str(shop.pk)
                content = set_token(shop_id)
                s_packed = ShopLogic.pack_shop(shop)
                s_packed.update(dict(token=content))
                return s_packed
            # 登录失败
            else:
                logging.info(
                    "SMS code validation for [%s]=[%s] failed, expected[%s]." % (tel, sms_code, sms_code_in_redis))
                raise ValueError("验证码验证失败.")
    # ==> 商户事件
    elif operation in ShopFSM.FE_INSIDE_EVENTS or operation in ShopFSM.OUTSIDE_EVENTS:
        # 对完善资料特殊添加时间信息
        if operation == ShopFSM.EVENT_COMPLETE_INFO and 'recommended_by' in kw:
            kw['recommended_by']['time'] = TimeZone.utc_now()
        # 对修改定价特殊处理: 能用tel找商户id
        if operation == ShopFSM.EVENT_ALTER_INFO:
            shop = Shop.objects(tel=kw.tel).first()
        # 其他事件一概用shop_id
        else:
            shop = Shop.objects(id=kw.shop_id).first()
        if shop:
            operator_type = kw.operator_type
            kw.pop('operator_type')
            modified_shop = ShopFSM.update_status(operator_type, shop, operation, **kw)
            if not modified_shop:
                raise ValueError(
                    "State transfer for shop[%s][%s][%s] using [%s] failed." % (
                        kw.shop_id, shop.name, shop.status, operation))
            return ShopLogic.pack_shop(modified_shop)

    else:
        pass


# === 金钱相关:充值,扣款 ===
@api
@post('/shop/web_top_up')
def api_shop_web_top_up():
    # shop_id, cash
    params = ctx.request.input()
    # 记录这次尝试
    transact_num = gen_transact_num()
    params.transact_num = transact_num
    s = Shop.objects(id=params.shop_id).first()
    params.shop_name = s.name
    params.shop_tel = s.tel
    TopUpLogic.create(**params)
    # 创建PC网页端充值接口链接
    url = create_web_trade(transact_num, params.cash)
    logging.info(url)
    # 返回示例 {
    #     "transact_num": "20160226117671",
    #     "url": "https://mapi.alipay.com/gateway.do?seller_email=abcx%40123feng.com&seller_id=2088901729140845"
    #            "&total_fee=0.01&service=create_direct_pay_by_user"
    #            "&_input_charset=utf-8&sign=d4ee6f2151e2a0aafce26865b4fb4ad9"
    #            "&out_trade_no=20160226117671&payment_type=1"
    #            "&notify_url=http%3A%2F%2F123.57.45.209%3A5000%2Fpay%2Falipay%2Fweb%2Fnotify"
    #            "&sign_type=MD5&partner=2088901729140845&subject=charge",
    # }
    return {
        'transact_num': transact_num,
        'url': url
    }


@api
@post('/shop/wap_top_up')
def api_shop_wap_top_up():
    # 输入: shop_id, cash
    kw = ctx.request.input()
    # 记录这次尝试
    transact_num = gen_transact_num()
    kw.transact_num = transact_num
    s = Shop.objects(id=kw.shop_id).first()
    kw.shop_name = s.name
    kw.shop_tel = s.tel
    TopUpLogic.create(**kw)
    # 创建手机wap充值接口链接
    url = create_wap_trade(transact_num, kw.cash, '商户充值')
    logging.info(url)
    # 返回示例 {'transact_num': transact_num,
    #         'url': 'http://wappaygw.alipay.com/service/rest.htm?service=alipay.wap.auth.authAndExecute
    # &format=xml&v=2.0&_input_charset=utf-8
    # &req_data=<auth_and_execute_req><request_token>20160226c760e7d843186665408fa6729ee21979</request_token>
    # </auth_and_execute_req>&sec_id=MD5&partner=2088901729140845&sign=f7d02ce9ece212677a512108687594fb}
    return {
        'transact_num': transact_num,
        'url': url
    }


@api
@post('/shop/app_top_up')
def api_shop_app_top_up():
    # shop_id, cash
    kw = ctx.request.input()
    # 记录这次尝试
    transact_num = gen_transact_num()
    kw.transact_num = transact_num
    s = SyncAccount.get_basic_from_id(kw.shop_id)
    kw.shop_name = s['name']
    kw.shop_tel = s['tel']
    TopUpLogic.create(**kw)
    return {
        'transact_num': transact_num,
        'notify_url': WEB_NOTIFY_URL  # 回调接口
    }


@api
@get('/shop/h5/js_sdk_signature')
def api_shop_h5_get_js_sdk_signature():
    kw = Schema({
        'noncestr': schema_unicode,
        'timestamp': schema_int,
        'url': schema_unicode  # 当前网页的URL，不包含#及其后面部分
    }).validate(ctx.request.input())
    jsapi_ticket = redis_client.get(key_jsapi_ticket)
    # 如果过期了, 重新获取jsapi_ticket
    if not jsapi_ticket:
        access_token = redis_client.get(key_access_token)
        if not access_token:
            access_token, expire_in = get_access_token()
            redis_client.setex(key_access_token, access_token, expire_in)
        jsapi_ticket = get_jsapi_ticket(access_token)
        redis_client.setex(key_jsapi_ticket, jsapi_ticket, 7200)
    return get_js_sdk_signature(kw['noncestr'], jsapi_ticket, kw['timestamp'], kw['url'])


@api
@post('/shop/h5/wx_top_up')
def api_shop_h5_wx_top_up():
    kw = Schema({
        'shop_id': schema_unicode,
        'cash': schema_float_2,
        'code': schema_unicode,  # 用于获取用户标识openid
    }).validate(ctx.request.input())
    code = kw.pop('code')
    # 记录这次尝试
    transact_num = gen_transact_num()
    kw.transact_num = transact_num
    s = Shop.objects(id=kw.shop_id).first()
    kw.shop_name = s.name
    kw.shop_tel = s.tel
    TopUpLogic.create(**kw)
    # 创建预支付交易会话, 获取预支付交易会话标识
    result = wx_generate_prepay_jsapi(transact_num, kw['cash'], ctx.request.remote_addr, code)
    if result['result'] == 'success':
        return {
            'prepay_id': result['prepay_id'],
        }
    else:
        raise ValueError('wxPay[JSAPI] Error: %s' % result['msg'])


# === 商户直接微信/支付宝转账支付
@api
@post('/shop/native/wx_pay')
def api_shop_native_wx_pay():
    """
    注意: 使用所有微信相关的接口都要记得改默认的超时时间, 微信接口调用非常的慢!
    :return:
    """
    kw = Schema({
        'shop': {
            'id': schema_unicode,
            'name': schema_unicode_empty,
            'tel': schema_unicode_empty,
        },
        'cash': schema_float_2
    }).validate(ctx.request.input())
    # 记录这次尝试
    transact_num = gen_transact_num()
    shop = kw['shop']
    TopUpLogic.create(transact_num=transact_num,
                      shop_id=shop['id'], shop_name=shop['name'], shop_tel=shop['tel'],
                      cash=kw['cash'])
    # 创建预支付交易会话, 获取微信支付二维码
    result = wx_generate_prepay_native(transact_num, kw['cash'])
    if result['result'] == 'success':
        return {
            'transact_num': transact_num,
            'code_url': result['code_url']
        }
    else:
        raise ValueError('wxPay[NATIVE] Error: %s' % result['msg'])


@api
@post('/shop/native/alipay')
def api_shop_native_alipay():
    """
    生成支付宝支付二维码
    :return:
    """
    kw = Schema({
        'shop': {
            'id': schema_unicode,
            'name': schema_unicode_empty,
            'tel': schema_unicode_empty,
        },
        'cash': schema_float_2
    }).validate(ctx.request.input())
    # 记录这次尝试
    transact_num = gen_transact_num()
    shop = kw['shop']
    TopUpLogic.create(transact_num=transact_num,
                      shop_id=shop['id'], shop_name=shop['name'], shop_tel=shop['tel'],
                      cash=kw['cash'])
    # 创建预支付交易会话, 获取支付宝支付二维码
    result = alipay_generate_prepay_native(transact_num, kw['cash'])
    if result['result'] == 'success':
        return {
            'transact_num': transact_num,
            'code_url': result['code_url']
        }
    else:
        raise ValueError('AliPay[NATIVE] Error: %s' % result['msg'])


@api
@post('/shop/wap_transfer')
def api_shop_wap_top_up_as_pay():
    # shop_id, cash
    kw = ctx.request.input()
    # 记录这次尝试
    transact_num = gen_transact_num()
    s = Shop.objects(id=kw.shop_id).first()

    # todo 暂时用充值尝试的记录
    TopUpLogic.create(transact_num=transact_num, shop_id=kw.shop_id, shop_name=s.name, shop_tel=s.tel, cash=kw.cash)
    # 创建手机wap转账接口链接
    url = gen_wap_transfer_link(transact_num, kw.cash, '商户现金支付')
    logging.info(url)
    return {
        'transact_num': transact_num,
        'url': url
    }


@api
@post('/shop/wap_transfer_callback')
def api_shop_wap_transfer_callback():
    kw = ctx.request.input()
    logging.info("[WAP-TRANSFER]Alipay callback request-body=%s." % kw)

    result = wap_transfer_notice_handler(kw)

    if result['result'] == 'success':
        FlowLogic.transfer_success(**result)
        logging.info('[WAP-TRANSFER] success.')
    else:
        FlowLogic.notified_of_failure(**result)
        logging.info('[WAP-TRANSFER] failure.')
    return 'success'


@api
@post('/shop/native/wx_pay_callback')
def api_shop_native_wx_pay_callback():
    # 给微信支付的第三方回调
    body = ctx.request.get_body()
    logging.info('[WX-PAY]wxPay callback request-body=%s' % body)

    result = wx_callback(body)
    if result['result'] == 'success':
        msg = FlowLogic.transfer_success(**result)
        return {
            'ret': generate_xml({'return_code': 'SUCCESS'}),
            'msg': msg,
            'transact_num': result['transact_num'],
            'trade_no': result['trade_no']
        }
    else:
        msg = FlowLogic.notified_of_failure(**result)
        return {
            'ret': generate_xml({'return_code': 'FAIL'}),
            'msg': msg
        }


@api
@post('/shop/native/alipay_callback')
def api_shop_native_alipay_callback():
    # 给支付宝扫二维码支付的第三方回调
    body = ctx.request.get_body()
    logging.info('[ALI-PAY]AliPay callback request-body=%s' % body)

    result = alipay_native_callback(body)
    if result['result'] == 'success':
        msg = FlowLogic.transfer_success(**result)
        return {
            'ret': 'success',
            'msg': msg,
            'transact_num': result['transact_num'],
            'trade_no': result['trade_no']
        }
    else:
        msg = FlowLogic.notified_of_failure(**result)
        return {
            'ret': 'success',
            'msg': msg
        }


# == 充值相关回调 ==
@api
@post('/shop/web_app_top_up_callback')
def api_shop_web_top_up_callback_post():
    params = ctx.request.input()
    logging.info("[WEB/APP]Alipay callback request-params=%s." % params)

    result = web_trade_notice_handler(params)
    # 充值成功: 记录result到对应的充值记录; 记录到流水表; 更新商户余额
    if result['result'] == 'success':
        FlowLogic.top_up_success(**result)
    # 充值失败: 记录result到对应的充值记录;
    else:
        FlowLogic.notified_of_failure(**result)
    return 'success'


@api
@post('/shop/wap_top_up_callback')
def api_shop_wap_top_up_callback_post():
    # 给支付宝充值的第三方回调
    params = ctx.request.input()
    logging.info("[WAP-TOP-UP]Alipay callback request-params=%s." % params)

    # result,out_trade_no=>transact_num
    result = wap_trade_notice_handler(params)

    # 充值成功: 记录result到对应的充值记录; 记录到流水表; 更新商户余额
    if result['result'] == 'success':
        FlowLogic.top_up_success(**result)
    # 充值失败: 记录result到对应的充值记录;
    else:
        FlowLogic.notified_of_failure(**result)
    return 'success'


@api
@post('/shop/wx_top_up_callback')
def api_shop_wxpay_top_up_callback():
    # 给微信支付的第三方回调
    body = ctx.request.get_body()
    logging.info('[WX-TOP-UP]wxPay callback request-body=%s' % body)

    # result, out_trade_no => transact_num
    result = wx_callback(body)
    if result['result'] == 'success':
        msg = FlowLogic.top_up_success(**result)
        return {
            'ret': generate_xml({'return_code': 'SUCCESS'}),
            'msg': msg
        }
    else:
        msg = FlowLogic.notified_of_failure(**result)
        return {
            'ret': generate_xml({'return_code': 'FAIL'}),
            'msg': msg
        }


# == 检查对应流水号是否已经成功支付 ==
@api
@get('/shop/check_transact')
def api_shop_check_transact():
    params = Schema({
        'transact_num': schema_unicode
    }).validate(ctx.request.input())
    tu = TopUpLogic.find_first('trade_no,result', 'where transact_num=?', params['transact_num'])
    if tu:
        return tu
    else:
        return {'result': 'not-yet', 'trade_no': ''}


@api
@post('/shop/cash_flow')
def api_shop_cash_flow():
    """
    @api {post} /shop/cash_flow [商户]扣款/退款
    @apiName api_shop_cash_flow
    @apiGroup shop

    @apiParam {string(6)} transact_type 交易类型, 只能是（`PAY`, `REFUND`）中的任意一个.
    @apiParam {string(24)} shop_id 商户id, 如 "56c2d708a785c90ab0014d00".
    @apiParam {decimal} cash 充值金额（元）,精确到小数点后2位, ROUND_DOWN.

    @apiParamExample {json} 请求示例:
    Request Method: POST
    Request URL: http://123.57.45.209:9099/shop/cash_flow
    Request Body:
        {
            "transact_type": "pay",
            "shop_id": "56c2d708a785c90ab0014d00",
            "cash": 0.01
        }
    @apiSuccessExample {string} 扣款/退款成功返回交易流水号示例:
        HTTP/1.1 200 OK
        "20160301151746"
    @apiErrorExample {json} 失败示例:
        HTTP 400 ValueError:
        {
            "message": "error message"
        }
    """
    params = ctx.request.input()
    # 交易类型检查: 'PAY', 'REFUND'
    if safe_str(params.transact_type).strip().upper() not in ('PAY', 'REFUND'):
        raise ValueError("transact_type[%s] should be in ('PAY', 'REFUND')." % params.transact_type)
    params.transact_type = safe_str(params.transact_type).strip()
    # 金额检查:
    if 'cash' not in params:
        raise ValueError("Should provide me with params [cash] and [shop_id] in body.")
    cash = round(decimal.Decimal(params.cash, 2), 2)
    if cash <= 0.0:
        raise ValueError("cash[%s] should be at least [0.01]." % params.cash)
    params.cash = cash
    # 扣款: 记录到流水表; 更新商户余额;
    params.transact_num = gen_transact_num()
    params.transact_type = str(params.transact_type).upper()
    if params.transact_type == TRANSACT_TYPE.PAY:
        return FlowLogic.deduct(**params)
    elif params.transact_type == TRANSACT_TYPE.REFUND:
        return FlowLogic.refund(**params)


@api
@post('/shop/flow/complex_query')
def api_retrieve_flow():
    """
    @api {post} /shop/flow/complex_query/:page [商户]资金流水复杂查询
    @apiDescription 查询商户余额,消费金额等.
    @apiName api_retrieve_flow
    @apiGroup shop

    @apiParam {list} filter_col `["shop_id", "cash" ...]`. 表`flow`中的字段列表. `[]`表示取所有字段.
    @apiParam {str} [group_by] 按照什么来group by. 表`flow`中的字段. 如`shop_id`.
    @apiParam {str} op `AND`或者`OR`. 表示如何组合过滤条件.
    @apiParam {int} is_not 如果有这个key, 则表示该字段上的过滤条件要取非.
    @apiParam {int} page 2. 表示第二页, 从1开始. [1:2147483648), 分页查. <=20条数据, 一次返回所有; >20条, 一次返回20条.

    @apiParamExample {json} 请求body示例:
        {
            "filter_col": ["shop_id", "sum(cash) as paid"],
            "query":
                {
                    "op": "AND",
                    "exprs": [
                        {"shop_id": {"in": ["56c2d708a785c90ab0014d00", "56c2d708a785c90ab0014d00"]}},
                        {"type": {"like": "%PAY%"}},
                        {"is_not":1, "shop_name": {"like": "%测试%"}}
                    ]
                },
            "group_by": "shop_id"
        }
    @apiParamExample {json} 对于"query"部分的解释 expr_json_example:
        expr_json_atom = {
            "op": "AND",
            "exprs": [
                {"shop_id": {"in": ["56c2d708a785c90ab0014d00", "56c2d708a785c90ab0014d00"]}},
                {"type": {"like": "%PAY%"}},
                {"is_not":1, "shop_name": {"like": "%测试%"}}
            ]
        }

        expr_json_level_2 = {
            "op": "OR",
            "exprs": [
                expr_json_atom,
                # expr_json_atom,
            ]
        }

    @apiSuccessExample {json} 成功示例(filter_col列表长度是1,即查询单个值时):
        HTTP/1.1 200 OK
        [0.01, 0.02, 0.5, 0.0]

    @apiSuccessExample {json} 成功示例(filter_col列表长度大于1,即查询多个值时):
        HTTP/1.1 200 OK
        [
            {
                "shop_id": "56c2d708a785c90ab0014d00",
                "paid": 0.23
            }
        ]
    """
    filter_col_str, where, limit, args = complex_query(ctx.request.input())
    flows = FlowLogic.find_by(filter_col_str, where, limit, *args)
    _count = FlowLogic.found_rows(filter_col_str, where, *args)
    ctx.response.set_header("X-Resource-Count".encode('utf-8'), _count)
    return flows


@api
@post('/shop/flow_statistics/complex_query')
def api_retrieve_flow_stats():
    filter_col_str, where, group_by_limit, args = complex_query(ctx.request.input())
    return FlowStatisticsLogic.find_by(filter_col_str, where, group_by_limit, *args)


# === 一些仅用在这里的api的函数 ===
def gen_transact_num():
    return utc_8_day().replace('-', '') + shortuuid.ShortUUID().random(length=6)
