# -*- coding:utf-8 -*-
import hashlib
import platform
import time
import traceback
import urllib

import requests

BAIDU_SETTINGS = {
    "android": {
        "api_key": "Af2vGeB2H0negdwVK5GOpv3G",
        "secret_key": "INLINPTeGIFGaGyxRukEfFp3QnOWem5l"
    },
    "ios": {
        "api_key": "HdjeXkuf8aSim4jZGG0Z83IQ",
        "secret_key": "eFoCqF5g0QXKSNYAT4CkvjwllyGV5czG"
    }
}

PUSH_URL = "http://channel.api.duapp.com/rest/2.0/channel/channel"
PUSH_URL_V3 = "http://api.push.baidu.com/rest/3.0/push/single_device"
METHOD = "POST"
PLATFORM_ANDROID = 3
PLATFORM_IOS = 4
BAIDU_SETTINGS_V3 = {
    PLATFORM_ANDROID: {
        "api_key": "Af2vGeB2H0negdwVK5GOpv3G",
        "secret_key": "INLINPTeGIFGaGyxRukEfFp3QnOWem5l"
    },
    PLATFORM_IOS: {
        "api_key": "HdjeXkuf8aSim4jZGG0Z83IQ",
        "secret_key": "eFoCqF5g0QXKSNYAT4CkvjwllyGV5czG"
    }
}


def baidu_push(token, msg, platform='android', env='develop'):
    """
    核心服务内部接口, 不对外提供。调用百度云推送2.0的接口
    百度文档地址: http://developer.baidu.com/wiki/index.php?title=docs/cplat/push/api/list
    param token: 百度的user_id，设备token
    param msg: 推送的消息体
    param platform: 平台, android/ios
    param env: 环境, develop/product
    return: True/False
    """

    # 拼装百度接口的参数
    params = {}
    params['method'] = 'push_msg'
    params['apikey'] = BAIDU_SETTINGS[platform]['api_key']
    params['push_type'] = 1
    params['user_id'] = token
    params['messages'] = msg
    params['message_type'] = 0
    params['timestamp'] = time.time()
    if platform == 'android':
        params['msg_keys'] = 'android'
        params['device_type'] = 3
    elif platform == 'ios':
        params['message_type'] = 1  # 注释掉这行使ios的推送发送消息而不是通知
        params['msg_keys'] = 'ios'
        params['device_type'] = 4
        params['deploy_status'] = 1 if env == 'develop' else 2
    params['sign'] = cal_sign(params, platform)

    # 调用百度接口进行消息推送
    try:
        r = requests.post(PUSH_URL, data=params, timeout=5)
    except Exception:
        print traceback.format_exc()
        return False
    response = r.json()
    print response
    if response.get("response_params", {}).get("success_amount", ""):
        return True
    else:
        return False


def cal_sign(params, platform='android'):
    keys_list = sorted(params.keys())
    params_list = []
    for key in keys_list:
        params_list.append("%s=%s" % (key, params[key]))
    params_str = "".join(params_list)
    sign_str = METHOD + PUSH_URL + params_str + BAIDU_SETTINGS[platform]['secret_key']
    encode_str = urllib.quote_plus(sign_str.encode("utf-8"))
    return hashlib.md5(encode_str).hexdigest().upper()


def __cal_sign(params, device_type=PLATFORM_ANDROID):
    params_str = "".join(
        [
            "{k}={v}".format(k=key, v=params[key])
            for key in sorted(params.keys())
            ]
    )
    sign_str = METHOD + PUSH_URL_V3 + params_str + BAIDU_SETTINGS_V3[device_type]['secret_key']
    encode_str = urllib.quote_plus(sign_str)
    return hashlib.md5(encode_str).hexdigest()


def baidu_push_v3(channel_id, msg, device_type=PLATFORM_ANDROID):
    """
    文档: http://push.baidu.com/doc/restapi/restapi?qq-pf-to=pcqq.c2c
    :param channel_id:
    :param msg:
    :param device_type:
    :return:
    """
    params = {
        'apikey': BAIDU_SETTINGS_V3[device_type]['api_key'],
        'secretKey': BAIDU_SETTINGS_V3[device_type]['secret_key'],
        'expires': 300,
        'timestamp': int(time.time()),
        'device_type': str(device_type),
        'msg_type': 0 if device_type == PLATFORM_ANDROID else 1,
        'channel_id': str(channel_id),
        'msg': msg
    }
    # 1：开发状态；2：生产状态
    params['deploy_status'] = 1
    params['sign'] = __cal_sign(params, device_type)

    # 调用百度接口进行消息推送
    try:
        headers = {
            'content-type': 'application/x-www-form-urlencoded;charset=utf-8',
            'user-agent': 'BCCS_SDK/3.0' +
                          str(platform.uname()) +
                          'python/2.7.3 (Baidu Push Server SDK V3.0.0) cli/Unknown'
        }
        r = requests.post(PUSH_URL_V3, data=urllib.urlencode(params), headers=headers, timeout=5)
    except Exception as e:
        print traceback.format_exc()
        return False, {'error': str(e)}
    response = r.json()

    if "response_params" in response:
        return True, {}
    else:
        return False, response


if __name__ == '__main__':
    from tools_lib.common_util.archived.gtz import TimeZone

    msg = {
        "source": "deliver",
        "type": "force_deliver_notice",
        "content": {
            "title": u"测试",
            "body": u"同志们好，首长好",
            "create_time": TimeZone.datetime_to_str(TimeZone.utc_now()),
        }
    }

    print baidu_push_v3('3737072413124982526', msg, device_type=PLATFORM_ANDROID)
