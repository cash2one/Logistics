#coding=utf-8
__author__ = 'kk'

import json
import logging
from tornado import gen

from tools_lib.gedis.gedis import Redis
from tools_lib.gtornado.web2 import ReqHandler
from tools_lib.windchat import conf

from utils.answerer_utils import pack_leancloud_callback_to_ws
from utils import channel_utils, message_utils

redisc = Redis()


class LeancloudChannelMessageCallback(ReqHandler):
    """
    给leancloud调用的频道对话回调
    """
    @gen.coroutine
    def post(self):
        # =========> verify token firstly <=========
        try:
            token = self.get_query_argument("token")
        except:
            logging.error("No token connection declined.")
            logging.info("data: %s" % self.request.body)
            self.resp_unauthorized("no token, no way.")
            return
        if token!=conf.LC_CALLBACK_TOKEN_CURRENT:
            self.resp_unauthorized("Bad token.")
            logging.error("Bad token: %s, should be: %s" % (token, conf.LC_CALLBACK_TOKEN_CURRENT))
            return
        # 更新未读
        a = yield pack_leancloud_callback_to_ws(self.get_body_args())
        for i in a:
            logging.info(i["message"])
            channel_utils.CP_unread_increase(
                i["cli"],
                f=i["from"],
                t=conf.CHANNEL_PRESENCE_ANY_CLIENT_ID,
                last_message=message_utils.pack_message_summary(i["message"])
            )
        packed = yield pack_leancloud_callback_to_ws(self.get_body_args())
        # 直接扔给 web socket 处理了
        redisc.publish(conf.TREDIS_CHANNEL_CURRENT, json.dumps(packed))
        self.resp_created()