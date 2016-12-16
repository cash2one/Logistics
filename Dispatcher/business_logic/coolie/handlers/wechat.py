# coding: utf-8
from __future__ import unicode_literals

import logging
from tornado import gen
from wechat_sdk import WechatBasic, messages

from tools_lib.gtornado.web2 import ReqHandler
from tools_lib.wx_mp.conf import WECHAT_CONF


# ===> 微信公众号事件处理 <===
class WeChatEventHandler(ReqHandler):
    @gen.coroutine
    def post(self):
        wb = WechatBasic(conf=WECHAT_CONF)
        msg = wb.parse_data(self.get_body_args())
        if isinstance(msg, messages.EventMessage):
            # 判断是事件消息
            print(msg)
        self.resp()
