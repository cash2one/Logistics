#coding=utf-8
__author__ = 'kk'

from tornado import gen

from tools_lib.gtornado import async_requests
from tools_lib.windchat import conf

try:
    import ujson as json
except:
    import json


# ============================== 可缓存 ==============================

@gen.coroutine
def query_account(account=None, client_id=None, full_resp=False):
    """
    查询账户信息
    """
    url = conf.WC_DAS_PREFIX + "/windchat/das/account/query"
    if account:
        resp = yield async_requests.post(url, json={
            "account": account,
            "full_resp": full_resp
        })
    elif client_id:
        resp = yield async_requests.post(url, json={
            "client_id": client_id,
            "full_resp": full_resp
        })
    else:
        resp = yield async_requests.post(url, json={
            "full_resp": full_resp
        })
    raise gen.Return(json.loads(resp.body))


# ============================== 不缓存 ==============================

@gen.coroutine
def create_account(account_id, account_type):
    """
    创建聊天账户
    """
    url = conf.WC_DAS_PREFIX + "/windchat/das/account"
    yield async_requests.post(url, json={
        "account_id": account_id,
        "account_type": account_type
    })
