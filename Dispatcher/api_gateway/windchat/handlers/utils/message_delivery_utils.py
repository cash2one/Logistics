#coding=utf-8
__author__ = 'kk'

import json
import logging
from schema import Schema, SchemaError, Use, And, Or, Optional

from tools_lib.leancloud import sdk
from tools_lib.leancloud.credentials import credentials
from tools_lib.gtornado.escape import schema_int, schema_utf8, schema_utf8_empty, schema_bool
from tools_lib.windchat import conf

from . import channel_utils


def deliver_channel_message(body):
    """
    同步发送频道消息
    :param body:
    """
    logging.info(body)
    if body["type"]==conf.MQ_TYPE_SEND_NOW:
        rtm_obj = sdk.Rtm(**credentials)
        data = Schema([
            {
                Optional("from_peer", default=conf.SYSTEM_ANSWERER_CLIENT_ID): schema_utf8,
                "to_peers": Use(list), # TODO 官方文档指定批量发送的极限为20, 这里每20个人请求一次
                "message":{
                    Optional("talker_avatar", default=""): schema_utf8_empty,
                    Optional("talker_name", default=conf.SYSTEM_ANSWERER_NAME): schema_utf8_empty,
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
                Optional("conv_id", default=conf.ALERT_CHANNEL_CURRENT): schema_utf8 # TODO 目前所有人的默认频道一样,将来会不一样,这里就有逻辑要处理了
            }
        ]).validate(body["data"])
        for msg in data:
            for one_peer in msg["to_peers"]:
                channel_utils.CP_unread_increase(msg["conv_id"], msg["from_peer"], one_peer)
            msg["message"] = json.dumps(msg["message"]) # leancloud规定 message 实体为文本而非 json 结构

            # 拆分to_peers
            to_peers = msg["to_peers"]
            to_peers_list = []
            while to_peers:
                to_peers_list.append(to_peers[:20])
                del to_peers[:20]
            for i in to_peers_list:
                msg["to_peers"] = i
                rtm_obj.send_message(**msg)
