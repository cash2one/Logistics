# coding=utf-8
__author__ = 'kk'
__all__ = ["wc_send_msg"]
'''
发送风信 快捷方式

'''

import json

from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPClient

import account
import channel_chat
import conf
from tools_lib.gtornado.http_code import is_success

async_cli = AsyncHTTPClient()
normal_cli = HTTPClient()


def account_query(**kwargs):
    """
    根据账户查询
    :param account: 见account.req_query
    :return:
    """
    resp = normal_cli.fetch(account.req_query(**kwargs), raise_error=False)
    if not is_success(resp.code):
        return False
    return json.loads(resp.body)


@gen.coroutine
def tornado_account_query(**kwargs):
    """
    根据账户查询
    :param account: 见account.req_query
    :return:
    """
    resp = yield async_cli.fetch(account.req_query(**kwargs), raise_error=False)
    if not is_success(resp.code):
        raise gen.Return(False)
    raise gen.Return(json.loads(resp.body))


def channel_send_message(client_id, message_type=conf.MSG_TYPE_PLAIN_TEXT, conv_id=conf.ALERT_CHANNEL_CURRENT, **kwargs):
    """
    给多人批量发单条消息
    :param client_id: 可以是一个 client_id, 也可以是 list
    :param msg: 消息结构内容, 具体结构参见msg_doc
    """
    to_peers = []
    if isinstance(client_id, (str, unicode)):
        to_peers.append(client_id)
    elif isinstance(client_id, list) or isinstance(client_id, set) or isinstance(client_id, tuple):
        to_peers = client_id
    else:
        assert 0
    wc_msg_list = channel_chat.WCChannelMessage()
    wc_msg_list.append({
        "message": {
            "message_type": message_type,
            "message": kwargs
        },
        "to_peers": to_peers,
        "conv_id": conv_id
    })
    wc_msg_list.send_now()
