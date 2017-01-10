# coding:utf-8

import base64
import json
import logging
from urllib.parse import parse_qs

from . import alipay_config
from . import alipay_wap_util
import arrow
import requests
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from tools_lib import host_info
from urllib.parse import parse_qs

# 支付宝 open-api 统一入口
ALIPAY_OPENAPI_GATEWAY = "https://openapi.alipay.com/gateway.do"

# 统一收单线下交易预创建
METHOD_TRADE_PRECREATE = "alipay.trade.precreate"

# 回调接口
if host_info.DEBUG:
    PAY_NOTIFY_URL = 'http://dev.api.gomrwind.com:5000/shop/alipay_callback'
else:
    PAY_NOTIFY_URL = 'http://api.gomrwind.com:5000/shop/alipay_callback'


def rsa_verify(public_key, paras, sign):
    """验证 rsa 返回"""
    pub_key = RSA.importKey(public_key)
    paras = alipay_wap_util.filter_param(paras)
    paras = alipay_wap_util.create_link_string(paras, True, False)
    verifier = PKCS1_v1_5.new(pub_key)
    data = SHA.new(paras.encode('utf-8'))
    return verifier.verify(data, base64.b64decode(sign))


def _generate_sign(private_key, **kwargs):
    """
    计算支付宝支付的签名
    """
    origin_sign_list = ["%s=%s" % (item[0], item[1]) for item in sorted(kwargs.items())]
    origin_sign_combined = "&".join(origin_sign_list)
    key = RSA.importKey(private_key)
    h = SHA.new(origin_sign_combined.encode('utf-8'))
    signer = PKCS1_v1_5.new(key)
    return base64.b64encode(signer.sign(h))


def _base_open_api_params(method, **kwargs):
    """
    ali-pay request generator
    :param kwargs:
    :return: dict to generate a json
    """
    all_params = {
        "app_id": alipay_config.APP_ID,
        "method": method,
        "charset": "UTF-8",
        "sign_type": "RSA",
        "timestamp": arrow.now().format("YYYY-MM-DD HH:mm:ss"),
        "version": "1.0",
        "biz_content": json.dumps(kwargs)
    }
    all_params.update(kwargs)
    all_params["sign"] = _generate_sign(private_key=alipay_config.APP_PRIVATE_KEY, **all_params)
    print((json.dumps(all_params)))
    return all_params


def alipay_generate_prepay_native(transact_num, cash, subject="客户支付"):
    """
    获取支付宝的付款二维码
    :param transact_num: 交易号
    :param cash: 金额(float)
    :param subject: 显示在交易内容里面
    """

    resp = requests.post(ALIPAY_OPENAPI_GATEWAY, data=_base_open_api_params(
        method=METHOD_TRADE_PRECREATE,
        notify_url=PAY_NOTIFY_URL,
        biz_content=json.dumps({
            "out_trade_no": transact_num,
            "seller_id": alipay_config.PARTNER,
            "total_amount": cash,
            "subject": subject
        })
    ))
    content = json.loads(resp.content.decode("gbk"))
    logging.warn(content)
    if content["alipay_trade_precreate_response"]["msg"] == "Success":
        return {
            'result': 'success',
            'code_url': content["alipay_trade_precreate_response"]["qr_code"]
        }
    else:
        return {
            'result': 'failure',
            'msg': content["alipay_trade_precreate_response"]["msg"]
        }


def alipay_native_callback(req_body):
    """
    支付宝付款之后的回调信息处理
    :param req_body: dict (body 是url-encoded的 body 而非 json!)
    转化成dict
        {
            'app_id': ['2016062801559836'],
            'buyer_id': ['2088002639242866'],
            'buyer_logon_id': ['boi***@gmail.com'],
            'buyer_pay_amount': ['0.01'],
            'fund_bill_list': ['[{"amount":"0.01","fundChannel":"ALIPAYACCOUNT"}]'],
            'gmt_create': ['2016-07-02 17:28:04'],
            'gmt_payment': ['2016-07-02 17:29:21'],
            'invoice_amount': ['0.01'],
            'notify_id': ['4ce25fc441f41256c739acc5121957bmmy'],
            'notify_time': ['2016-07-02 17:29:21'],
            'notify_type': ['trade_status_sync'],
            'open_id': ['20880007586019226542668712218486'],
            'out_trade_no': ['20160702CgmXcW'],
            'point_amount': ['0.00'],
            'receipt_amount': ['0.01'],
            'seller_email': ['abcx@123feng.com'],
            'seller_id': ['2088901729140845'],
            'sign': [
                'qD2/LXPDd2inxsWFT1uPIrHB3wqA71Um1qJGHD7MEz9X42KViqb33nqOccXt7CZEXUO16mB+aTiMxQKGWYiLyWMtR9kwf+9v0XOloE5zVG42obMsEelJHzXHcCtHVVYcKblF4XuFmEQ4wGvGkFiBXbASMJ8J+WuH7ad6GJmimXc='],
            'sign_type': ['RSA'],
            'subject': ['\xbf\xcd\xbb\xa7\xd6\xa7\xb8\xb6'],
            'total_amount': ['0.01'],
            'trade_no': ['2016070221001004860227842176'],
            'trade_status': ['TRADE_SUCCESS']
        }
    """
    req_body = parse_qs(req_body)
    req_body_kv = {k: req_body[k][0] for k in req_body}
    # TODO STEP 1. 验证回调签名
    # sign = req_body_kv["sign"]
    # verified = rsa_verify(alipay_config.APP_PUBLIC_KEY, req_body_kv, sign)
    # if not verified:
    #     return {
    #         'result': 'failure',
    #         'transact_num': req_body["out_trade_no"][0],
    #         'trade_no': req_body["trade_no"][0],
    #         "reason": "RSA sign not verified!"
    #     }
    # TODO STEP 2. 验证通知id
    resp = requests.get(alipay_config.ALIPAY_GATEWAY_NEW, params={
        "service": "notify_verify",
        "partner": alipay_config.PARTNER,
        "notify_id": req_body_kv["notify_id"]
    })
    if resp.content!="true":
        return {
            'result': 'failure',
            'transact_num': req_body["out_trade_no"][0],
            'trade_no': req_body["trade_no"][0],
            "reason": "Notify_id not verified!"
        }
    try:
        return {
            'result': 'success',
            'transact_num': req_body["out_trade_no"][0],
            'trade_no': req_body["trade_no"][0],
            'amount': req_body["total_amount"][0],  # unicode
            'pay_time': arrow.get(req_body["gmt_payment"][0]).datetime
        }
    except:
        return {
            'result': 'failure',
            'transact_num': req_body["out_trade_no"][0],
            'trade_no': req_body["trade_no"][0],
        }
