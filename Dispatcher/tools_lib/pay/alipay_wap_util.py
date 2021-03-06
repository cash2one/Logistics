# coding:utf-8

import base64
import urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET
from hashlib import md5

from . import alipay_config as ac
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


# === 以下是现金支付(即转账后不记账户余额,只记录消费)
def build_wap_handshake_query_str(order_no, amount, desc):
    # 按照格式填参数
    req_data = ('<direct_trade_create_req>'
                '<notify_url>%s</notify_url>'
                '<call_back_url>%s</call_back_url>'
                '<seller_account_name>%s</seller_account_name>'
                '<out_trade_no>%s</out_trade_no>'
                '<subject>%s</subject>'
                '<total_fee>%s</total_fee>'
                '</direct_trade_create_req>') % (ac.WAP_TRANS_NOTIFY_URL, '', ac.EMAIL, order_no, desc, amount)
    param = {
        'service': 'alipay.wap.trade.create.direct',
        'partner': ac.PARTNER,
        '_input_charset': ac.INPUT_CHARSET,
        'sec_id': ac.SIGN_TYPE,
        'format': 'xml',
        'v': '2.0',
        'req_id': order_no,
        'req_data': req_data,
    }
    # 去掉空值和签名信息
    param = filter_param(param)
    param['sign'] = sign(param)
    param['sec_id'] = ac.SIGN_TYPE
    ls = create_link_string(param, False, False)
    return ls.encode('utf-8')


def build_wap_do_trade_query_str(token):
    req_data = '<auth_and_execute_req><request_token>%s</request_token></auth_and_execute_req>' % token
    param = {
        'req_data': req_data,
        'service': 'alipay.wap.auth.authAndExecute',
        'partner': ac.PARTNER,
        'sec_id': ac.SIGN_TYPE,
        '_input_charset': ac.INPUT_CHARSET,
        'v': '2.0',
        'format': 'xml',
    }
    param = filter_param(param)
    param['sign'] = sign(param)
    param['sec_id'] = ac.SIGN_TYPE
    return create_link_string(param, False, False)


# === 以下是充值 ===
def build_request(type, *args, **kwargs):
    if type == 'trade':
        para = build_wap_handshake_param(ac.WAP_TOP_UP_NOTIFY_URL, *args, **kwargs)
    elif type == 'execute':
        para = build_do_trade_param(*args, **kwargs)
    para = filter_param(para)
    para['sign'] = sign(para)
    para['sec_id'] = ac.SIGN_TYPE
    return create_link_string(para, False, False)


def build_wap_handshake_param(notify_url, order_no, amount, desc):
    req_data = ('<direct_trade_create_req>'
                '<notify_url>%s</notify_url>'
                '<call_back_url>%s</call_back_url>'
                '<seller_account_name>%s</seller_account_name>'
                '<out_trade_no>%s</out_trade_no>'
                '<subject>%s</subject>'
                '<total_fee>%s</total_fee>'
                '</direct_trade_create_req>') % (notify_url, '', ac.EMAIL, order_no, desc, amount)
    param = {
        'service': 'alipay.wap.trade.create.direct',
        'partner': ac.PARTNER,
        '_input_charset': ac.INPUT_CHARSET,
        'sec_id': ac.SIGN_TYPE,
        'format': 'xml',
        'v': '2.0',
        'req_id': order_no,
        'req_data': req_data,
    }
    return param


def build_do_trade_param(token):
    req_data = '<auth_and_execute_req><request_token>%s</request_token></auth_and_execute_req>' % token
    param = {
        'req_data': req_data,
        'service': 'alipay.wap.auth.authAndExecute',
        'partner': ac.PARTNER,
        'sec_id': ac.SIGN_TYPE,
        '_input_charset': ac.INPUT_CHARSET,
        'v': '2.0',
        'format': 'xml',
    }
    return param


def parse_response(response_str, sign_type=ac.SIGN_TYPE):
    """对response做解析"""
    if sign_type == '0001':
        # TODO
        pass
    root = ET.fromstring(response_str)
    return {child.tag: child.text for child in root.getchildren()}


def sign(para, type=ac.SIGN_TYPE):
    """签名, 目前只支持md5签名
    @param para dict
    @return 签名 str"""
    para = filter_param(para)
    para_str = create_link_string(para, True, False)
    # print 'sign.....', para_str
    if type == 'MD5':
        return md5_sign(para_str)
    elif type in ('0001', 'RSA'):
        return rsa_sign(para_str)


def md5_sign(para_str):
    """对请求参数做md5签名"""
    original = '%s%s' % (para_str, ac.KEY)
    return md5(original.encode('utf-8')).hexdigest()


def rsa_sign(para_str):
    """对请求参数做rsa签名"""
    key = RSA.importKey(ac.PRIVATE_KEY)
    h = SHA.new(para_str.encode('utf-8'))
    signer = PKCS1_v1_5.new(key)
    return base64.b64encode(signer.sign(h))


def verify(paras, sign, wap_async=False):
    """对签名做验证"""
    if ac.SIGN_TYPE == 'MD5':
        return md5_verify(paras, sign, wap_async)
    elif ac.SIGN_TYPE in ('0001', 'RSA'):
        return rsa_verify(paras, sign)


def md5_verify(paras, sign, wap_async=False):
    """对签名做md5验证"""
    paras = filter_param(paras)
    if wap_async:
        para_str = create_wap_async_notice_str(paras)
    else:
        para_str = create_link_string(paras, True, False)
    return md5_sign(para_str) == sign


def rsa_verify(paras, sign):
    """对签名做rsa验证"""
    pub_key = RSA.importKey(ac.ALIPAY_PUBLIC_KEY)
    paras = filter_param(paras)
    paras = create_link_string(paras, True, False)
    verifier = PKCS1_v1_5.new(pub_key)
    data = SHA.new(paras.encode('utf-8'))
    return verifier.verify(data, base64.b64decode(sign))


def rsa_decrypt(paras):
    """对支付宝返回参数解密"""
    key = RSA.importKey(ac.PRIVATE_KEY)
    key = PKCS1_OAEP.new(key)
    decrypted = key.decrypt(base64.b64decode(paras.get('notify_data')))
    paras['notify_data'] = decrypted
    return paras


def filter_param(paras):
    """过滤空值和签名"""
    for k, v in list(paras.items()):
        if not v or k in ['sign', 'sign_type']:
            paras.pop(k)
    return paras


def create_link_string(paras, sort, encode):
    """对参数排序并拼接成query string的形式"""
    if sort:
        paras = sorted(list(paras.items()), key=lambda d: d[0])
    if encode:
        return urllib.parse.urlencode(paras)
    else:
        if not isinstance(paras, list):
            paras = list(paras.items())
        ps = ''
        for p in paras:
            if ps:
                ps = '%s&%s=%s' % (ps, p[0], p[1])
            else:
                ps = '%s=%s' % (p[0], p[1])
        return ps


def create_wap_async_notice_str(paras):
    """这个字符串既不是排序后的顺序，又不是原始顺序，而是固定顺序。坑爹的支付宝文档"""
    service = paras.get('service')
    v = paras.get('v')
    sec_id = paras.get('sec_id')
    notify_data = paras.get('notify_data')
    return 'service=%s&v=%s&sec_id=%s&notify_data=%s' % (service, v, sec_id, notify_data)
