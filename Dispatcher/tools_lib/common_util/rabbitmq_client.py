# coding:utf-8

import pika
import pika_pool
from tools_lib.host_info import *

#####################################################
# exchange 名称
EXCHANGE_PUSH_MSG = 'push_msg'
EXCHANGE_SEND_SMS = 'send_sms'
EXCHANGE_POST_GPS = 'post_gps'
EXCHANGE_WINDCHAT4_0 = "windchat4_0"
EXCHANGE_WINDCHAT4_1 = "windchat4_1"

#####################################################
# queue 名称
QUEUE_PUSH_MSG = 'q_push_msg'
QUEUE_SEND_SMS = 'q_send_sms'
QUEUE_POST_GPS = 'q_post_gps'
QUEUE_NEW_TOKEN = 'q_new_token'

#####################################################
# type 类型
# 广播
TYPE_FANOUT = 'fanout'
# 单播
TYPE_DIRECT = 'direct'
# 组播
TYPE_TOPIC = 'topic'


RABBITMQ_SERVER = {
    PROD_API_NODE: {
        "host": LOCALHOST_IP,
        "port": 5672,
    },
    'default': {
        "host": DEV_OUTER_IP,
        "port": 5672,
    },
}


class RabbitMqCtl(object):
    """ 使用连接池 """
    __pool_dict = {}

    @classmethod
    def basic_publish(cls, exchange='', routing_key='', body='', server_node=None):
        """
        消息发送
        @param exchange:
        @param routing_key:
        @param body:
        @param server_node: 要连接到的rabbitmq服务器node
        @return:
        """
        if server_node is None:
            server_node = CURRENT_NODE if CURRENT_NODE in RABBITMQ_SERVER else 'default'
        if server_node not in cls.__pool_dict:
            cls.__pool_dict[server_node] = pika_pool.QueuedPool(
                create=lambda: pika.BlockingConnection(pika.ConnectionParameters(**RABBITMQ_SERVER[server_node])),
                max_size=10,
                max_overflow=10,
                timeout=5,
                recycle=3600,
                stale=60,
            )
        print(("Connecting to rabbitmq server @%s" % RABBITMQ_SERVER[server_node]))
        with cls.__pool_dict[server_node].acquire() as connection:
            connection.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,    # make message persistent
                )
            )