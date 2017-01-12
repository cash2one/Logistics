#coding=utf-8
__author__ = 'kk'

import logging
from tornado import gen
from tools_lib.gtornado.web2 import ReqHandler
from .utils.message_delivery_utils import deliver_channel_message


class ChannelMsgDeliveringHandler(ReqHandler):
    @gen.coroutine
    def post(self):
        data = self.get_body_args()
        deliver_channel_message(data)
        self.resp_created()
