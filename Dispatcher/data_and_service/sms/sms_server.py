# coding:utf-8
from __future__ import unicode_literals
import pickle
import sys
import traceback

import os
import pika
import arrow

# === 模块自己的PYTHON_PATH, 让代码找到正确的tools_lib. ==>要在所有import前做!!!
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from tools_lib.common_util.rabbitmq_client import EXCHANGE_SEND_SMS, TYPE_FANOUT
from tools_lib.common_util.third_party.sms_api import send_sms


def callback(ch, method, properties, body):
    """
    @api {baisc_publish} 交换机(EXCHANGE_SEND_SMS) 短信发送服务
    @apiVersion 0.1.0
    @apiName SmsService
    @apiGroup Service

    @apiParam {string} tel 手机号
    @apiParam {string} msg 短信内容
    @apiParam {int=1(普通),2(验证码)} type=1 短信类型
    @apiParam {int} [code] 验证码

    """
    try:
        data = pickle.loads(body)
        print("[%s] %s %s" % (arrow.now().format(fmt='MM-DD HH:mm:ss'), data['tel'], data['msg']))

        # sms_type = data.get('type', 1)
        # if sms_type == 2:
        #     # 验证码, 10分钟过期
        #     redis_client.set(key_sms_code.format(tel=data['tel']), data['code'], ex=10 * 60)
        # 发送短信
        send_sms(data['tel'], data['msg'])
    except Exception as e:
        print(traceback.format_exc())


if __name__ == '__main__':
    print('[{current_time}] starting server ...'.format(current_time=arrow.now().format('MM-DD HH:mm:ss')))

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE_SEND_SMS, type=TYPE_FANOUT)
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=EXCHANGE_SEND_SMS, queue=queue_name)
    channel.basic_consume(callback, queue=queue_name, no_ack=True)
    channel.start_consuming()
