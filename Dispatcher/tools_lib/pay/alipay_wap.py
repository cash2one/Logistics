# coding:utf-8
from __future__ import unicode_literals
import logging
import urllib
import xml.etree.ElementTree as ET

import re
import requests
from alipay_config import WAP_GATEWAY, ALIPAY_VERIFY_URL, DEAL_STATUS, PARTNER
from alipay_wap_util import build_wap_handshake_query_str, build_wap_do_trade_query_str, build_request, rsa_decrypt, verify


def create_wap_trade(transact_num, money, desc):
    """
    创建请求支付宝的URL
    :param transact_num: 充值流水号
    :param money: 交易金额
    :param desc: 交易备注
    :return: 支付宝请求的URL
    """
    # TODO
    # 判断订单是否合法（是否已被支付等）

    desc = '123feng.com'
    para = build_request('trade', transact_num, money, desc)
    resp_obj = requests.post(WAP_GATEWAY, params=para)
    resp = urllib.unquote(resp_obj.content)
    tmp = re.findall('<request_token>(.+)</request_token>', resp)
    if tmp:
        # TODO
        # 创建支付宝交易流水

        token = tmp[0]
        params = build_request('execute', token)
        return '%s?%s' % (WAP_GATEWAY, params)
    else:
        # 失败
        pass


def wap_sync_notice(get_args):
    """
    处理alipay服务器在手机web支付交易完成后以GET请求发送的同步通知
    :param get_args: http请求中的GET参数
    :return:
        验证成功返回
        {
            "status": "success",
            "transact_num": "321321321"
        }
        验证失败返回
        {
            "status": "fail",
            "transact_num": "321321321"
        }
    """
    # http://123.57.45.209:5000/shop/top_up_callback
    # ?out_trade_no=20160222184275
    # &request_token=requestToken
    # &result=success
    # &trade_no=2016022221001004860207205672
    # &sign=ac765fc36c8426fc003e5af556102368
    # &sign_type=MD5
    valid = verify(get_args, get_args.get('sign'))
    if valid:
        # 返回如下格式http响应
        return {
            'result': 'success',
            'transact_num': get_args.get('out_trade_no'),
            'trade_no': get_args.get('trade_no')
        }
    else:
        # 返回如下格式http响应
        return {
            'result': 'failure',
            'transact_num': get_args.get('out_trade_no'),
            'trade_no': get_args.get('trade_no')
        }


def _verify_resp(notify_id):
    """验证response是不是支付宝发出。其实签名就已经能比较好的保证了，这步操作可能是为了防止秘钥泄露的签名伪造"""
    url = '%s&partner=%s&notify_id=%s' % (ALIPAY_VERIFY_URL, PARTNER, notify_id)
    print url
    resp = requests.get(url)
    if resp.content == 'true':
        return True
    else:
        return False


def wap_trade_notice_handler(post_args):
    """
    处理alipay服务器在手机web支付交易完成后以POST请求发送的异步通知, 请求结束返回 success 字符串
    支付宝收到包含该字符串的响应后，就认为这次业务逻辑结束
    :param post_args: 支付宝POST请求的参数
    :return: "success"
    """
    success, failure = 'success', 'failure'

    sign_type = post_args.get('sec_id')
    if sign_type == '0001':
        # 这种签名的数据需要解密
        post_args = rsa_decrypt(post_args)
    notify_data = post_args.get('notify_data', '')
    root = ET.fromstring(notify_data.encode('utf-8'))
    notify_dict = {child.tag: child.text for child in root.iter()}

    # 验证签名和response有效性
    if not (verify(post_args, post_args['sign'], True) and _verify_resp(notify_dict.get('notify_id'))):
        raise ValueError("Verification failed")
    status = DEAL_STATUS.get(notify_dict.get('trade_status'), 0)
    transact_num = notify_dict.get('out_trade_no')

    # 支付宝返回支付失败
    if status not in (DEAL_STATUS['TRADE_FINISHED'], DEAL_STATUS['TRADE_SUCCESS']):
        ret = {
            'result': failure,
            'transact_num': transact_num,
            'trade_no': notify_dict.get('trade_no')
        }
    else:
        ret = {
            'result': success,
            'transact_num': transact_num,
            'trade_no': notify_dict.get('trade_no'),
            'amount': notify_dict.get('total_fee'),
            'buyer_id': notify_dict.get('buyer_id'),
            'pay_time': notify_dict.get('gmt_payment')
        }
    return ret


# === 商户直接转账支付 ===
def gen_wap_transfer_link(transact_num, cash, desc):
    """
    生成请求支付宝转账的url
    :param transact_num: 转账流水号
    :param cash: 交易金额
    :param desc: 交易备注
    :return: 支付宝请求的url
    """
    desc = '123feng.com'
    gateway_param = build_wap_handshake_query_str(transact_num, cash, desc)
    resp_obj = requests.post(WAP_GATEWAY, params=gateway_param, timeout=7.5)
    resp = urllib.unquote(resp_obj.content)
    tmp = re.findall('<request_token>(.+)</request_token>', resp)
    if tmp:
        token = tmp[0]
        query_str = build_wap_do_trade_query_str(token)
        return '%s?%s' % (WAP_GATEWAY, query_str)
    else:
        logging.error('生成请求支付宝转账支付的url失败: 没有token.')
        return None


def wap_transfer_notice_handler(post_args):
    """
    处理alipay服务器在手机web支付交易完成后以POST请求发送的异步通知, 请求结束返回 success 字符串
    支付宝收到包含该字符串的响应后，就认为这次业务逻辑结束
    :param post_args: 支付宝POST请求的参数
    :return: "success"
    """
    sign_type = post_args.get('sec_id')
    if sign_type == '0001':
        # 这种签名的数据需要解密
        post_args = rsa_decrypt(post_args)
    notify_data = post_args.get('notify_data', '')
    root = ET.fromstring(notify_data.encode('utf-8'))
    notify_dict = {child.tag: child.text for child in root.iter()}

    # 验证签名和response的有效性
    if not (verify(post_args, post_args['sign'], True) and _verify_resp(notify_dict.get('notify_id'))):
        raise ValueError('Verification failed')
    status = DEAL_STATUS.get(notify_dict.get('trade_status'), 0)
    transact_num = notify_dict.get('out_trade_no')

    # 支付宝返回支付失败
    if status not in (DEAL_STATUS['TRADE_FINISHED'], DEAL_STATUS['TRADE_SUCCESS']):
        ret = {
            'result': 'failure',
            'transact_num': transact_num,
            'trade_no': notify_dict.get('trade_no')
        }
    else:
        ret = {
            'result': 'success',
            'transact_num': transact_num,
            'trade_no': notify_dict.get('trade_no'),
            'amount': notify_dict.get('total_fee'),
            'buyer_id': notify_dict.get('buyer_id'),
            'pay_time': notify_dict.get('gmt_payment')
        }
    return ret

if __name__ == '__main__':
    alipay_notice_args = {'v': '1.0', 'sign': '01dc7d5d108ef6d746d53ec3e31d22df',
                          'notify_data': '<notify><payment_type>1</payment_type><subject>123feng.com</subject><trade_no>2016032921001004370206978744</trade_no><buyer_email>15058115878</buyer_email><gmt_create>2016-03-29 17:49:50</gmt_create><notify_type>trade_status_sync</notify_type><quantity>1</quantity><out_trade_no>20160329Uh9eRR</out_trade_no><notify_time>2016-03-29 17:49:51</notify_time><seller_id>2088811364424201</seller_id><trade_status>TRADE_SUCCESS</trade_status><is_total_fee_adjust>N</is_total_fee_adjust><total_fee>0.01</total_fee><gmt_payment>2016-03-29 17:49:51</gmt_payment><seller_email>abcf@123feng.com</seller_email><price>0.01</price><buyer_id>2088502576717374</buyer_id><notify_id>6c545823879d141a0156e338c595a51iuu</notify_id><use_coupon>N</use_coupon></notify>',
                          'service': 'alipay.wap.trade.create.direct', 'sec_id': 'MD5'}
    print(wap_trade_notice_handler(alipay_notice_args))
