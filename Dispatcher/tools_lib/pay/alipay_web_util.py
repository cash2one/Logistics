# coding:utf-8
# 支付宝即时到账接口

from hashlib import md5
from urllib.parse import urlencode
import requests
from . import alipay_config as ac


def create_direct_pay_by_user(tn, subject, total_fee):
    """

    :param tn: 系统内的订单号
    :param subject: 交易商品名称
    :param total_fee: 交易金额
    :return: 返回url字符串, 出错返回None
    """
    try:
        params = dict()
        params.update({
            ##################################################
            #  基本参数
            # 接口名称 *
            "service": "create_direct_pay_by_user",
            # 合作者身份 *
            "partner": ac.PARTNER,
            # 参数编码字符集 *
            "_input_charset": ac.INPUT_CHARSET,
            # 服务器异步通知信息
            "notify_url": ac.WEB_NOTIFY_URL,
            # 页面跳转同步通知页面路径
            "return_url": '',
            ##################################################
            # 业务参数
            # 系统内的订单号 *
            "out_trade_no": str(tn),
            # 商品名称 *
            "subject": subject,
            # 支付类型 *
            "payment_type": str(ac.PAYMENT_TYPE['buy']),
            # 交易金额 *
            "total_fee": total_fee,
            # 卖家支付宝用户号 *
            "seller_id": ac.PARTNER,
            # 卖家的支付宝账号
            "seller_email": ac.EMAIL,
        })

        params, prestr = params_filter(params)
        # 签名 *
        params['sign'] = sign(prestr, ac.KEY, ac.SIGN_TYPE)
        # 签名方式 *
        params['sign_type'] = ac.SIGN_TYPE

        return ac.ALIPAY_GATEWAY_NEW + urlencode(params)
    except Exception:
        return None


def params_filter(params):
    """
    对字典排序并剔除数组中的空值和签名参数
    :param params: 待排序的字典
    :return: 字典和字符串
    """
    ks = list(params.keys())
    ks.sort()
    new_params = dict()
    prestr = ''
    for k in ks:
        v = params[k]
        # 对键进行编码
        # k = smart_str(k, ac.INPUT_CHARSET)
        # 不签名sign和sign_type参数，并且参数值不为空
        if k not in ('sign', 'sign_type') and v:
            # 对值进行编码
            # v = smart_str(v, ac.INPUT_CHARSET)
            new_params[k] = v
            prestr += '%s=%s&' % (k, new_params[k])
    # 剔除末尾的&
    prestr = prestr[:-1]
    return new_params, prestr


def sign(prestr, key, sign_type=ac.SIGN_TYPE):
    """
    签名, 目前只支持md5签名
    :param prestr: 待签名的字符串
    :param key: 支付宝交易安全检验码
    :param sign_type: 签名类型
    :return: 签名后的字符串
    """
    # print "SIGN (%s).........." % prestr
    if sign_type == 'MD5':
        return md5(prestr + key).hexdigest()
    else:
        return ''


def notify_verity(params):
    """
    验证消息是否是支付宝发出的合法消息
    :return:
    """
    notify_id = params.get('notify_id')
    sign_str = params.get('sign', '')
    responseTxt = True
    if notify_id:
        responseTxt = notify_verify_response(notify_id)
    is_sign = notify_sign_verify(params, sign_str)
    return is_sign and responseTxt


def notify_sign_verify(params, sign_str):
    """
    根据反馈回来的信息，生成签名结果
    :return:
    """
    new_params, prestr = params_filter(params)
    is_sign = False
    if params['sign_type'] == ac.SIGN_TYPE:
        is_sign = MD5.verify(prestr, sign_str)
    return is_sign


def notify_verify_response(notify_id):
    """
    获取远程服务器ATN结果,验证返回URL
    :param notify_id:
    :return:
    """
    verify_url = ac.ALIPAY_VERIFY_URL + "partner=" + ac.PARTNER + "&notify_id=" + notify_id
    try:
        resp = requests.get(verify_url)
        if resp.content == 'true':
            return True
    except:
        return False


class MD5(object):
    @staticmethod
    def verify(text, sign_str):
        my_sign = md5('%s%s' % (text, ac.KEY)).hexdigest()
        return sign_str == my_sign


def settle(deal):
    """支付成功后清算"""
    pass
