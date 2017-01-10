#coding=utf-8
__author__ = 'kk'
__all__ = ["req_create", "req_query_client_id"]
'''
风信账户

======================================
WARNING 警告:仅允许AG层和BL层访问!请严格遵守
======================================
'''

import json
import logging
from tornado.httpclient import HTTPRequest
from .conf import WC_DAS_PREFIX, timeouts


def req_create(account_id, account_type):
    """
    创建leancloud聊天账户
    :param account_id: 内部账户ID,字串
    :param account_type: 账户类型,字串,可为空
    :return: client_id,即账户在leancloud的唯一ID
    """
    url = WC_DAS_PREFIX + "/windchat/das/account"
    return HTTPRequest(
        url,
        method="POST",
        body=json.dumps({
            "account_id": account_id,
            "account_type": account_type
        }),
        headers={"Content-Type": "application/json"},
        **timeouts
    )


def req_query(account=None, client_id=None):
    """
    {account_id, account_type} <=> {client_id}互相查
    :param account: {"account_id":"", "account_type":""}或者其 list,返回 client_id 的 list
    :param client_id: client_id 或者 client_id 的 list, 返回 account
    """
    url = WC_DAS_PREFIX + "/windchat/das/account/query"
    if account:
        to_query = {
            "account": account
        }
    elif client_id:
        to_query = {
            "client_id": client_id
        }
    else:
        raise Exception("Need at least one of account or client_id")
    return HTTPRequest(
        url,
        method="POST",
        body=json.dumps(to_query),
        headers={"Content-Type": "application/json"},
        **timeouts
    )
