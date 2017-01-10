# coding:utf-8


import json
import logging
import pickle

import requests
from requests.auth import HTTPBasicAuth
from tools_lib.common_util.rabbitmq_client import RabbitMqCtl, EXCHANGE_SEND_SMS
from tools_lib.common_util.sstring import safe_unicode
from tools_lib.gedis.gedis import Redis

SEND_SMS_TOO_MUCH = 1
SEND_SMS_SUCCESS = 2
SEND_SMS_FAIL = 3

LUOSIMAO_URL = "https://sms-api.luosimao.com/v1/send.json"
LUOSIMAO_PWD = "ca904c8c3c081149eb546abd4fae5156"

# 云片网络的短信接口
# yunpian_apikey = 'f2331bfd85886e65ed198209a87df829'
# yunpian_request_url = 'http://yunpian.com/v1/sms/send.json'
# yunpian_request_headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
# yunpian_response_code_ok = 0

MRWIND = "【风先生】"
# 同一手机号60秒只能发一次短信
# LIMIT_SEC = 60

# 短信类型
SMS_TYPE_NORMAL = 1
SMS_TYPE_VERIFICATION_CODE = 2

redis_client = Redis()


def async_send_sms(tel, msg="", sms_type=SMS_TYPE_NORMAL, code=0):
    tel = safe_unicode(tel)
    msg = safe_unicode(msg)
    sms_data = {
        'tel': tel,
        'type': sms_type,
    }

    if sms_type is SMS_TYPE_NORMAL:
        sms_data['msg'] = msg
    elif sms_type is SMS_TYPE_VERIFICATION_CODE:
        sms_data['code'] = code
        sms_data['msg'] = '您的验证码是{code}(有效期10分钟)'.format(code=code)
    else:
        raise Exception('无效的短信类型')
    RabbitMqCtl.basic_publish(exchange=EXCHANGE_SEND_SMS, body=pickle.dumps(sms_data))


def send_code(tel, code):
    # 输入: 手机号(str), 6位验证码(str/int)
    if not check_tel(tel):
        return False
    msg = '您的验证码是{code}(有效期10分钟)'.format(code=code)
    msg = _check_msg(msg)
    return _luosimao_send_sms(tel, msg)


def check_tel(tel):
    """
    检查手机号合法性
    检查规则: 11位并且以1开头的数字
    @param tel:
    @return:
    """
    return tel.isdigit() and tel.startswith('1') and len(tel) == 11


def send_sms(tel, msg):
    # 控制短信发送频率
    # key = key_sms_rate_limit.format(tel=tel)
    # if redis_client.exists(key):
    #     return False
    # redis_client.set(key, 1, ex=LIMIT_SEC)

    # 检查手机号合法性
    if not check_tel(tel):
        return False
    msg = _check_msg(msg)

    return _luosimao_send_sms(tel, msg)


def _check_msg(msg):
    return msg if MRWIND in msg else " ".join([msg, MRWIND])


def _luosimao_send_sms(tel, msg):
    tel = str(tel)
    url = LUOSIMAO_URL
    key = "api"
    passwd = LUOSIMAO_PWD
    data = {
        "mobile": tel,
        "message": msg
    }
    auth = HTTPBasicAuth(key, passwd)
    response = requests.post(url, data=data, auth=auth)
    result = json.loads(response.content)

    err = result.get("error")
    if str(err) == str(0):
        info = "[luosimao] 发送[%s][%s]成功." % (tel, msg)
        logging.info(info.encode('utf-8'))
        return SEND_SMS_SUCCESS
    else:
        warn = "[luosimao] 发送[%s][%s]失败. error=[%s]." % (tel, msg, err)
        logging.warning(warn.encode('utf-8'))
        return SEND_SMS_FAIL

# def _yunpian_send_sms(tels, msg):
#     if not isinstance(tels, list):
#         tels = [tels]
#     request_body_data = {
#         'apikey': yunpian_apikey,
#         'mobile': ','.join([safe_utf8(tel) for tel in tels]),
#         'text': safe_utf8(tel)
#     }
#     response = requests.post(
#         url=yunpian_request_url,
#         headers=yunpian_request_headers,
#         data=request_body_data
#     )
#     ret_msg = json.loads(response.content)
#     if ret_msg.get('code') is yunpian_response_code_ok:
#         return SEND_REGCODE_SUCCESS
#     else:
#         print msg
#         print ret_msg.get('detail')
#         return SEND_REGCODE_FAIL
