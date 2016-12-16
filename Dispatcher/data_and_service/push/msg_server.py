# -*- coding:utf-8 -*-
import json
import sys
import traceback

import os
import pika

# === 模块自己的PYTHON_PATH, 让代码找到正确的tools_lib. ==>要在所有import前做!!!
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from tools_lib.common_util.archived.baidu_push import baidu_push_v3, PLATFORM_ANDROID
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.common_util.rabbitmq_client import EXCHANGE_PUSH_MSG, TYPE_FANOUT
try:
    import cPickle as pickle
except:
    import pickle


def callback(ch, method, properties, body):
    """
    @api {baisc_publish} 队列(QUEUE_PUSH_MSG) 消息推送服务
    @apiVersion 0.1.0
    @apiName PushService
    @apiGroup Service

    @apiParam {obj} data 数据
    @apiParam {string} data.token 设备号(3.0版本中已废弃，不会有该字段)
    @apiParam {string} data.msg 消息内容
    @apiParam {string='android', 'ios'} [data.platform='android'] 平台
    @apiParam {string} data.channel_id 通道ID
    @apiParam {string='develop', 'product'} [data.env='develop'] 环境，ios才会用到
    """
    try:
        data = pickle.loads(body)
        # 把数据包装成列表
        if not isinstance(data, list):
            data = [data]

        for data_record in data:
            try:
                baidu_push_v3(
                    channel_id=data_record['channel_id'],
                    msg=json.dumps(data_record.get('msg', ''), ensure_ascii=False),
                    device_type=PLATFORM_ANDROID
                )
            except:
                pass
    except:
        print traceback.format_exc()
    finally:
        pass

if __name__ == '__main__':
    print '[{current_time}] starting server ...'.format(current_time=TimeZone.local_now())

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE_PUSH_MSG, type=TYPE_FANOUT)
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=EXCHANGE_PUSH_MSG, queue=queue_name)
    channel.basic_consume(callback, queue=queue_name, no_ack=True)
    channel.start_consuming()
