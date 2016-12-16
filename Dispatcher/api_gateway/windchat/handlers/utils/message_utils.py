#coding=utf-8
__author__ = 'kk'

import logging

from tools_lib.windchat import conf


def pack_message_summary(msg):
    """
    包装msg的摘要
    :param msg:
    :return:
    """
    logging.info(msg)
    if not msg:
        return ""
    msg_type = msg["message_type"]
    msg_body = msg["message"]
    if msg_type==conf.MSG_TYPE_PLAIN_TEXT:
        return msg_body["content"]
    elif msg_type==conf.MSG_TYPE_IMAGE:
        return "[图片]"
    elif msg_type==conf.MSG_TYPE_DELIVERY_ALERT:
        return msg_body["content"]
    elif msg_type==conf.MSG_TYPE_ROUTINE_ALTERED_ALERT:
        return msg_body["content"]
    else:
        # 缺省尝试
        logging.warn("Trying an unknown message type! Consider check types.")
        s = msg_body.get("summary", "")
        if not s:
            s = msg_body.get("content", "")
        if not s:
            s = "[消息]"
        return s