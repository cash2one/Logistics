#coding=utf-8
__author__ = 'kk'
__all__ = ["WCChannelMessage"]
'''
发送频道风信
'''
import json
import logging

import conf
from schema import Schema, Or, Use, Optional
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.common_util.rabbitmq_client import RabbitMqCtl
from tools_lib.gtornado.escape import schema_utf8, schema_utf8_empty, schema_int


class WCChannelMessage(list):
    """
    风信频道消息

    JSON({
        "type": "SEND-NOW"立刻发送
        "data":[
            {windchat-object},...
        ]
    })

    JSON({
        "type": "SCHEDULE"定时发送
        "scheduled_time": // 定时发送的时间(如果是定时发送的话),utc,形如"2016-12-12T12:12:12Z"
                          // 若非定时发送,这个键可以不出现在json里,或者为空字符串
        "data":[
            {windchat-object},...
        ]
    }) // 这种情况下,请求的返回会带有token, 凭 token 撤销此次操作

    JSON({
        "type": "SCHEDULE-CANCEL"取消定时发送
        "token": // 如果是scheduled类型定时发送,会返回一个token,如果需要取消定时发送,给出token的值,设置type为"SCHEDULE-CANCEL"即可
                 // 此时json只需要包括"type"和"token"即可
    })

    {windchat-object}:
    {
        "from_peer":           // 回答者client_id, str
        "to_peers":            // 用户在leancloud的client_ID,如果是群发(即指定了client_id_list),则该键可以不出现在json里
        "message": {
            "message_type": 1,
            "message": ""或者{},
            "talker_avatar": "",
            "talker_name": "姓名",
            "talker_id": "talker account id",
            "talker_type": "man" "shop" "staff" "answerer"
        }
        "conv_id":             // 频道cli
    }

    """
    def append(self, wc_message):
        wc_message = Schema({
            Optional("from_peer", default=conf.SYSTEM_ANSWERER_CLIENT_ID): schema_utf8,
            "to_peers": Use(list),
            "message":{
                Optional("talker_avatar", default=""): schema_utf8,
                Optional("talker_name", default=conf.SYSTEM_ANSWERER_NAME): schema_utf8,
                Optional("talker_id", default=conf.SYSTEM_ANSWERER_CLIENT_ID): schema_utf8,
                Optional("talker_type", default=conf.ACCOUNT_TYPE_STAFF): Or(lambda x:x in conf.ACCOUNT_TYPES),
                Optional("message_type", default=conf.MSG_TYPE_PLAIN_TEXT): schema_int,
                "message": {
                    Optional("title", default=""): schema_utf8_empty,
                    Optional("content", default=""): schema_utf8_empty,
                    Optional("summary", default=""): schema_utf8_empty,
                    Optional("description", default=""): schema_utf8_empty,
                    Optional("url", default=""): schema_utf8_empty,
                    Optional("id", default=""): schema_utf8_empty
                }
            },
            "conv_id": schema_utf8
        }).validate(wc_message)
        # 注意 message 内容必须 json 序列化
        # wc_message["message"] = json.dumps(wc_message["message"])
        # TODO 序列化的地方丢给风信服务
        super(WCChannelMessage, self).append(wc_message)

    def _send(self, json_data):
        logging.info(json_data)
        RabbitMqCtl.basic_publish(exchange=conf.CURRENT_EXCHANGE, body=json_data)

    def send_now(self):
        """
        立刻发送
        :return:
        """
        json_data = {
            "type": conf.MQ_TYPE_SEND_NOW,
            "data": self
        }
        return self._send(json.dumps(json_data))

    def schedule(self, scheduled_time):
        """
        定时发送
        :param scheduled_time:
        :return: schedule token for cancelling
        """
        json_data = {
            "type": conf.MQ_TYPE_SCHEDULE,
            "scheduled_time": TimeZone.datetime_to_str(scheduled_time),
            "data": self
        }
        return self._send(json.dumps(json_data))

    def schedule_cancel(self, token):
        """
        取消定时发送
        :param token:
        :return:
        """
        json_data = {
            "type": conf.MQ_TYPE_SCHEDULE_CANCEL,
            "token": token
        }
        return self._send(json.dumps(json_data))
