# coding: utf-8

import os
import hashlib
import requests
import platform
import logging
import xml.etree.ElementTree as Etree
from tools_lib.host_info import PROD_API_NODE

PREPAY_URL = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
# 公众号基础支持access_token, 用于生成jsapi_ticket, 不能太频繁调用, 要放redis
ACCESS_TOKEN_URL = 'https://api.weixin.qq.com/cgi-bin/token'
# 生成jsapi_ticket
# https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=ACCESS_TOKEN&type=jsapi
JSAPI_TICKET_URL = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket'
# 从前端传过来的code获取网页授权access_token
WEB_PAGE_AUTH_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'
# 微信回调接口
if platform.node() == PROD_API_NODE:
    TOP_UP_NOTIFY_URL = 'http://api.gomrwind.com:5000/shop/wx_top_up_callback'
    PAY_NOTIFY_URL = 'http://api.gomrwind.com:5000/shop/wx_pay_callback'
else:
    TOP_UP_NOTIFY_URL = 'http://dev.api.gomrwind.com:5000/shop/wx_top_up_callback'
    PAY_NOTIFY_URL = 'http://dev.api.gomrwind.com:5000/shop/wx_pay_callback'

# 密钥,加密相关
# APPID = 'wx3c8a09a82a74b651'
# MCH_ID = '1236086702'
# KEY = 'e44073b3e8d2e9181781d8d46e1c4d77'

APPID = 'wxeda2f6550280ac63'
MCH_ID = '1252235201'
KEY = 'e44073b3e8d2e9181781d8d46e1c4d77'
APP_SECRET = '8eef8247a26a7887a35ee5e887f38c50'  # 用于获取access_token

BODY = '客户充值'
# JSAPI--公众号支付、NATIVE--原生扫码支付、APP--app支付
TRADE_TYPE_JSAPI = 'JSAPI'
TRADE_TYPE_NATIVE = 'NATIVE'
SUCCESS = 'SUCCESS'
FAIL = 'FAIL'


def wx_generate_prepay_native(transact_num, cash):
    if cash <= 0:
        raise ValueError('cash[%s] should be a positive number.' % cash)

    # 给微信的参数列表
    params = {
        # 公众帐号ID
        "appid": APPID,
        # 商户号
        "mch_id": MCH_ID,
        # 随机字符串
        "nonce_str": ''.join([(hex(ord(x))[2:]) for x in os.urandom(16)]),
        # 商品描述
        "body": '客户支付',
        # 商户订单号
        "out_trade_no": transact_num,
        # 总金额: 单位为分
        "total_fee": int(cash * 100),
        # 终端IP
        # "spbill_create_ip": spbill_create_ip if spbill_create_ip else '222.129.57.103',
        # 通知地址
        "notify_url": PAY_NOTIFY_URL,
        # 交易类型
        "trade_type": TRADE_TYPE_NATIVE,
    }
    # 对所有参数进行签名计算后将签名加入参数列表
    sign = generate_sign(params)
    params['sign'] = sign
    params_xml = generate_xml(params)
    logging.info(params_xml)

    # 解析xml,判断预支付请求是否成功
    r = requests.post(url=PREPAY_URL, data=params_xml.encode('utf-8'))
    logging.info(r.content)
    wx_xml = Etree.fromstring(r.content)
    return_code = str(wx_xml.find('return_code').text)
    result_code = wx_xml.find('result_code')
    # 只有在return_code 和 result_code的时候才算是生成预支付成功
    # return_code 为通信标识, result_code 为操作标识
    if return_code == SUCCESS and hasattr(result_code, 'text') and str(result_code.text) == SUCCESS:
        return {
            'result': 'success',
            # 'prepay_id': wx_xml.find('prepay_id').text,
            'code_url': wx_xml.find('code_url').text,
        }
    else:
        return {
            'result': 'failure',
            'msg': wx_xml.find('return_msg').text
        }


def wx_generate_prepay_jsapi(transact_num, cash, spbill_create_ip, code):
    """
    调用微信的统一下单接口,生成预支付号返回给客户端
    :param transact_num:
    :param cash:
    :param spbill_create_ip: 微信要求终端设备的IP
    :param code: 用户同意授权，获取code. 参见 http://mp.weixin.qq.com/wiki/17/c0f37d5704f0b64713d5d2c37b468d75.html
    :return: {'prepay_id': 微信预支付号, 'order_num': 内部订单号}
    """
    if cash <= 0:
        raise ValueError('cash[%s] should be a positive number.' % cash)

    # 创建充值订单
    # new_charge_order = create_charge_order_quickly(app_id, user_id, amount, CHARGE_ORDER_TYPE)
    openid = get_openid(code)
    if not openid:
        return {
            'result': 'failure',
            'msg': 'invalid code'
        }

    # 给微信的参数列表
    params = {
        # 公众帐号ID
        "appid": APPID,
        # 商户号
        "mch_id": MCH_ID,
        # 随机字符串
        "nonce_str": ''.join([(hex(ord(x))[2:]) for x in os.urandom(16)]),
        # 商品描述
        "body": BODY,
        # 商户订单号
        "out_trade_no": transact_num,
        # 总金额: 单位为分
        "total_fee": int(cash * 100),
        # 终端IP
        # "spbill_create_ip": spbill_create_ip if spbill_create_ip else '222.129.57.103',
        # 通知地址
        "notify_url": TOP_UP_NOTIFY_URL,
        # 交易类型
        "trade_type": TRADE_TYPE_JSAPI,
        # 用户标识: trade_type=JSAPI，此参数必传
        "openid": openid,  # 'oUpF8uMuAJO_M2pxb1Q9zNjWeS6o',
    }
    # 对所有参数进行签名计算后将签名加入参数列表
    sign = generate_sign(params)
    params['sign'] = sign
    params_xml = generate_xml(params)
    logging.info(params_xml)

    # 解析xml,判断预支付请求是否成功
    r = requests.post(url=PREPAY_URL, data=params_xml.encode('utf-8'))
    # <xml>
    # <return_code><![CDATA[SUCCESS]]></return_code>
    # <return_msg><![CDATA[OK]]></return_msg>
    # <appid><![CDATA[wx3c8a09a82a74b651]]></appid>
    # <mch_id><![CDATA[1236086702]]></mch_id>
    # <nonce_str><![CDATA[yK4xomXXbvul2p05]]></nonce_str>
    # <sign><![CDATA[5D83D978D0788A0E5772268DF18A3AD3]]></sign>
    # <result_code><![CDATA[SUCCESS]]></result_code>
    # <prepay_id><![CDATA[wx20160613145805b670a19ea80562188743]]></prepay_id>
    # <trade_type><![CDATA[NATIVE]]></trade_type>
    # <code_url><![CDATA[weixin://wxpay/bizpayurl?pr=Kux0jUc]]></code_url>
    # </xml>
    logging.info(r.content)
    wx_xml = Etree.fromstring(r.content)
    return_code = str(wx_xml.find('return_code').text)
    result_code = wx_xml.find('result_code')
    # 只有在return_code 和 result_code的时候才算是生成预支付成功
    # return_code 为通信标识, result_code 为操作标识
    if return_code == SUCCESS and hasattr(result_code, 'text') and str(result_code.text) == SUCCESS:
        return {
            'result': 'success',
            'prepay_id': wx_xml.find('prepay_id').text,
            # 'code_url': wx_xml.find('code_url').text,
        }
    else:
        return {
            'result': 'failure',
            'msg': wx_xml.find('return_msg').text
        }


def wx_callback(post_args):
    """
    微信回调接口, 微信APP支付完成后后调用该接口
    :param post_args: 微信POST回调的请求参数
    :return: 对微信的返回值, 通过xml返回SUCCESS或FAIL
    """
    # 解析参数,xml格式
    wx_xml = Etree.fromstring(post_args)

    return_code = str(wx_xml.find('return_code').text)
    result_code = str(wx_xml.find('result_code').text)
    transact_num = wx_xml.find('out_trade_no').text
    total_fee = round(float(wx_xml.find('total_fee').text) / 100, 2)
    trade_type = str(wx_xml.find('trade_type').text)
    bank_type = str(wx_xml.find('bank_type').text)
    transaction_id = str(wx_xml.find('transaction_id').text)
    time_end = str(wx_xml.find('time_end').text)

    # 如果通信失败
    if return_code != SUCCESS:
        # return generate_xml({'return_code': FAIL})
        ret = {
            'result': 'failure',
            'transact_num': transact_num,
            'trade_no': transaction_id
        }
    else:
        ret = {
            'result': 'success',
            'transact_num': transact_num,
            'trade_no': transaction_id,
            'amount': total_fee,
            'pay_time': time_end
        }
    return ret
    # try:
    #     charge_order = ChargeOrder.objects.using(CHARGE_ORDER_BD).get(num=transact_num)
    #     wxpaydeal = WxpayDeal.get_by_order_num(transact_num=transact_num)
    # except Exception, e:
    #     return generate_xml({'return_code': SUCCESS})

    # TODO
    # 如果支付失败,则关闭订单
    # if result_code != SUCCESS:
    #     charge_order.status = CLOSED
    #     charge_order.save(update_fields=['update_time', 'status'])
    #     wxpaydeal.status = CLOSED
    #     wxpaydeal.save(update_fields=['update_time', 'status'])
    #     return HttpResponse(generate_xml({'return_code': SUCCESS}))

    # TODO
    # 微信可能会多次回调,先检查订单状态
    # if user_has_paid(transact_num):
    #     return HttpResponse(generate_xml({'return_code': SUCCESS}))

    # TODO
    # 更新商户账户和充值订单的状态,并记录微信返回的参数值

    # return generate_xml({'return_code': SUCCESS})


def get_openid(code):
    # 从前端传过来的code获取网页授权access_token
    resp_obj = requests.get(WEB_PAGE_AUTH_URL,
                            params=dict(grant_type='authorization_code', appid=APPID, secret=APP_SECRET, code=code))
    if resp_obj.status_code == 200:
        resp = resp_obj.json()
        logging.info('[get_openid] Got from wxPay: %s' % resp_obj.content)
        if 'errcode' in resp:
            return ''
        else:
            return resp['openid']
    else:
        logging.error('[get_openid] wxPay Error: %s' % resp_obj.content)
        return ''


def generate_sign(kwargs):
    """
    根据传入的字典计算微信支付的签名
    :param kwargs: dict
    :return: unicode
    """
    string_sign = ''
    for item in sorted(iter(kwargs.items()), key=lambda x: x[0]):
        sub = '%s=%s&' % item
        string_sign += sub
    string_sign = string_sign + 'key=' + KEY
    sign = hashlib.md5(string_sign.encode('utf-8')).hexdigest().upper()
    return str(sign)


def generate_xml(kwargs):
    """
    根据传入的字典生成xml的字符串
    :param kwargs: dict
    :return: unicode
    """
    xml_unicode = ''
    for key in kwargs:
        value = kwargs[key]
        # sub = '<%s><![CDATA[%s]]></%s>' % (key, value, key)
        sub = '<%s>%s</%s>' % (key, value, key)
        xml_unicode += sub
    xml_unicode = '<xml>%s</xml>' % xml_unicode
    return xml_unicode


# == 以下函数按顺序调用来生成JS-SDK权限验证的签名
def get_access_token():
    # 基础支持的access_token, 请勿过分频繁的调用哦, 存redis哦. ttl=7200
    resp_obj = requests.get(ACCESS_TOKEN_URL,
                            params=dict(grant_type='client_credential', appid=APPID, secret=APP_SECRET))
    if resp_obj.status_code == 200:
        resp = resp_obj.json()
        logging.info('[get_highly_secured_access_token] Got from wxPay: %s' % resp_obj.content)
        if 'errcode' in resp:
            return '', 0
        else:
            access_token = resp['access_token']
            expires_in = resp['expires_in']
            return access_token, expires_in
    else:
        logging.error('[get_highly_secured_access_token] wxPay Error: %s' % resp_obj.content)
        return '', 0


def get_jsapi_ticket(access_token):
    # 基础支持的jsapi_ticket, 请勿过分频繁的调用哦, 存redis哦. ttl=7200
    resp_obj = requests.get(JSAPI_TICKET_URL, params=dict(type='jsapi', access_token=access_token))
    if resp_obj.status_code == 200:
        resp = resp_obj.json()
        logging.info('[get_jsapi_ticket] Got from wxPay: %s' % resp_obj.content)
        if resp['errcode'] != 0:
            return ''
        else:
            return resp['ticket']
    else:
        logging.error('[get_jsapi_ticket] wxPay Error: %s' % resp_obj.content)
        return ''


def get_js_sdk_signature(noncestr, jsapi_ticket, timestamp, url):
    def generate_signature(kwargs):
        """
        根据传入的字典计算微信JS-SDK注入权限配置的signature
        :param kwargs: dict
        :return: unicode
        """
        string_sign = ''
        for item in sorted(iter(kwargs.items()), key=lambda x: x[0]):
            sub = '%s=%s&' % item
            string_sign += sub
        string_sign = string_sign + 'key=' + KEY
        sign = hashlib.sha1(string_sign.encode('utf-8')).hexdigest().upper()
        return str(sign)

    # 给微信的参数列表
    # noncestr=Wm3WZYTPz0wzccnW
    # jsapi_ticket=sM4AOVdWfPE4DxkXGEs8VMCPGGVi4C3VM0P37wVUCFvkVAy_90u5h9nbSlYy3-Sl-HhTdfl2fzFy1AOcHKP7qg
    # timestamp=1414587457
    # url=http://mp.weixin.qq.com?params=value
    params = {
        # 随机字符串
        "noncestr": noncestr,
        # 有效的jsapi_ticket
        "jsapi_ticket": jsapi_ticket,
        # 时间戳
        "timestamp": timestamp,
        # 当前网页的URL，不包含#及其后面部分
        "url": url,
    }
    # 对所有参数进行签名计算后将签名加入参数列表
    signature = generate_signature(params)
    return signature


if __name__ == '__main__':
    # print(get_highly_secured_access_token())
    # print(get_openid(code='001qjGmV1m0kX81orXnV1RvCmV1qjGm7'))  # 返回的openid形如: oNE91uBkiNf1YE8v-z_RkElmK2AE
    # print(get_jsapi_ticket(
    #     'lO-gRsFaf3jgfDS6iBsKtpaHaW7GNasSh9iq0WjD6iJRUYYnTBehWXUjdJ_eSqE1V0JR03JfSX03aeHiA3GaPxziGqj96UHcxU01OKWyYfsk43hl4JcLbinO-WbteY4wIUGiADAVHT'))

    print((
        get_js_sdk_signature(''.join([(hex(ord(x))[2:]) for x in os.urandom(16)]),
                             'sM4AOVdWfPE4DxkXGEs8VHI_iLGM64MRnq8nt6eZTP5dcEc2YoHFQMeQKy6LEJo3PhsXABkAeD0pgVdbtHFyxA',
                             1414587457, TOP_UP_NOTIFY_URL)))
