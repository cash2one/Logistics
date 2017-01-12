#coding=utf-8
__author__ = 'kk'

import logging

from .models import Account
from tools_lib.gtornado.web2 import ReqHandler

try:
    import ujson as json
except:
    import json


class AccountHandler(ReqHandler):
    def post(self):
        """
        @api {POST} /windchat/das/account 创建账户
        @apiDescription 创建新的风信(以及leancloud)账户
        @apiName das_wc_account_creation
        @apiGroup das_windchat
        @apiUse python_server_and_port_definition

        @apiParam (json) {string} account_id 内部账户id
        @apiParam (json) {string} account_type 类型账户("man"配送组, "shop"发货组, "staff"员工组)

        @apiParamExample {json} 请求示例
        {
            "account_id": "670b14728ad9902aecba32e22fa4f6bd",
            "account_type": "staff" // staff表示注册一个员工账号, 来源方 id 是"670b14728ad9902aecba32e22fa4f6bd"
        }

        @apiSuccessExample
            HTTP/1.1 201 Created
        """
        try:
            data = self.get_body_args()
            account_id = data["account_id"]
            account_type = data["account_type"]
        except:
            self.resp_error("bad json: failed when parsing schema")
            return
        obj = Account.create_account(account_id, account_type)
        self.resp_created(obj.format_response())


class AccountQueryHandler(ReqHandler):
    def post(self):
        """
        根据账户信息查询
        """
        data = self.get_body_args()
        account = data.get("account", None)
        client_id = data.get("client_id", None)
        full_resp = data.get("full_resp", False)
        if account:
            if isinstance(account, dict):
                account = [account]
            logging.warn(account)
            objs = Account.objects(account__in=account)
            if full_resp:
                self.resp([i.format_response() for i in objs])
            else:
                self.resp(list({i.client_id for i in objs})) # 默认查client_id的时候,仅返回client_id的list

        elif client_id:
            if isinstance(client_id, str):
                client_id = [client_id]
            objs = Account.objects(client_id__in=client_id)
            self.resp([i.format_response() for i in objs]) # 无论如何都是查account_id的时候,返回全部信息

        else:
            # 获取全部
            objs = Account.objects()
            if full_resp:
                self.resp([i.format_response() for i in objs])
            else:
                self.resp(list({i.client_id for i in objs})) # 默认返回client_id的 set
