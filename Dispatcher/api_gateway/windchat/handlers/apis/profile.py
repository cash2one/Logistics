#coding=utf-8
__author__ = 'kk'
"""
查询配送员\商户\员工的信息

注意:

* 请务必知道,这个模块是暂时的,未来应当是风信与业务逻辑彻底分离,所有人员数据存在风信的账户信息里
* 这个模块使用的 url 前缀应当与风信本身的分离
"""

import pickle
import logging
from tornado import gen
from tornado.httputil import url_concat

from tools_lib import host_info
from tools_lib.gtornado import async_requests
from tools_lib.windchat import conf
from tools_lib import java_account
from tools_lib.java_account import AsyncAccount

try:
    import ujson as json
except:
    import json


# ================== 配送线 ==================

@gen.coroutine
def get_all_man():
    """
    查询全部配送员
    :return:
    """
    mans = yield AsyncAccount.get_account_by_role(role_tag=java_account.ROLE_TAG_MAN)
    for i in mans:
        i["roleList"].append({"roleTag": "man"})
    raise gen.Return(mans)


@gen.coroutine
def get_man_by_account_id(account_id):
    """
    查询配送员
    :return:
    """
    # FIXME
    account_id = str(account_id)
    if account_id=="999999":
        raise gen.Return({
            "name": " 风信客服",
            "tel": "13245678901",
            "avatar": ""
        })
    elif account_id==conf.SYSTEM_ANSWERER_CLIENT_ID:
        raise gen.Return({
            "name": "系统通知",
            "tel": "13245678901",
            "avatar": ""
        })

    user = yield AsyncAccount.get_user_info_from_kwargs(id=account_id)
    raise gen.Return(user)


# ================== 发货线 ==================

@gen.coroutine
def get_all_shop():
    """
    查询全部商户
    :return:
    """
    shops = yield AsyncAccount.get_account_by_role(role_tag=java_account.ROLE_TAG_SHOP)
    for i in shops:
        i["roleList"].append({"roleTag": "shop"})
    raise gen.Return(shops)


@gen.coroutine
def get_shop_by_account_id(account_id):
    """
    查商户
    :return:
    """
    user = yield AsyncAccount.get_user_info_from_kwargs(id=account_id)
    raise gen.Return(user)



# ================== 职能线 ==================

@gen.coroutine
def staff_verify_token(token):
    """
    验证职能线 token,
    :param token:
    :return:
    """
    # url = conf.JAVA_SERVICE_PREFIX_CURRENT + "/WindCloud/staff/functionUser/token/check"
    # url = url_concat(url, {
    #     "accessToken": token
    # })
    # resp = yield async_requests.get(url, **conf.timeouts)
    # logging.info(resp.body)
    # raise gen.Return(json.loads(resp.body).get("user"))
    raise gen.Return({
        "name": "风信客服",
        "avatarQiniuHash": "默认客服头像.png",
        "staffNum": 999999
    })