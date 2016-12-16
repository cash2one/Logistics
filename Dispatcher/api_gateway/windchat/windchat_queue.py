#!/usr/bin/env python
# coding:utf-8
__author__ = 'kk'

import logging
import arrow
import sys
import traceback

import os
import pika

try:
    import ujson as json
except:
    import json

# === 模块自己的PYTHON_PATH, 让代码找到正确的tools_lib. ==>要在所有import前做!!!
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.common_util.rabbitmq_client import TYPE_FANOUT
from tools_lib.windchat.conf import CURRENT_EXCHANGE, MQ_HOST  # 根据当前代码的目录,选择应当使用的mq exchange


def callback(ch, method, properties, body):
    """
    风信转发
    body格式详见tools_lib.windchat.channel_chat
    """
    try:
        data = json.loads(body)
        from handlers.utils.message_delivery_utils import deliver_channel_message
        deliver_channel_message(data)
    except:
        logging.error("===== > callback  error < =====")
        logging.error(traceback.format_exc())


if __name__ == '__main__':
    logging.warn('[{current_time}] starting WindChat4 messaging server...'.format(current_time=arrow.now()))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=MQ_HOST))
    channel = connection.channel()

    channel.exchange_declare(exchange=CURRENT_EXCHANGE, type=TYPE_FANOUT)
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=CURRENT_EXCHANGE, queue=queue_name)
    channel.basic_consume(callback, queue=queue_name, no_ack=True)
    channel.start_consuming()
