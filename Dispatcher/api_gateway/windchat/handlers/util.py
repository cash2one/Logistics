#coding=utf-8
__author__ = 'kk'
"""

给产品、运营使用的工具接口,通常是通过 postman 直接调用,写的时候返回信息尽量用中文,不要要求太多输入的参数

"""

import logging
from schema import Schema, SchemaError, Use, Optional, And, Or
from tornado import gen

from tools_lib.gtornado.escape import schema_int, schema_bool, schema_utf8, schema_utf8_empty
from tools_lib.gtornado.web2 import ReqHandler
from tools_lib.windchat import conf

from . import apis.account
from .utils import message_delivery_utils


class SendChannelMsgToAllHandler(ReqHandler):
    @gen.coroutine
    def post(self):
        """
        给全部风信的用户发消息
        """
        try:
            data = Schema({
                "message": schema_utf8,
                "account_type": And(schema_utf8, lambda x:x in conf.ACCOUNT_TYPES)
            }).validate(self.get_body_args())
        except SchemaError:
            self.resp_error("格式错误。")
            return

        all_account = yield apis.account.query_account(full_resp=True)
        # 手动过滤出特定的账户类型
        all_client_id_list = [i["client_id"] for i in all_account if i["account_type"]==data["account_type"]]
        message_delivery_utils.deliver_channel_message({
            "type": conf.MQ_TYPE_SEND_NOW,
            "data": [
                {
                    "to_peers": all_client_id_list,
                    "message": {
                        "message": {
                            "content": data["message"],
                            "summary": data["message"]
                        }
                    }
                }
            ]
        })
        self.resp_created({"message": "完成。"})


class SendChannelMsgByTelHandler(ReqHandler):
    @gen.coroutine
    def post(self):
        """
        给指定的手机号发风信
        """
        self.resp_created({"message": "完成。"})
