#coding=utf-8
__author__ = 'kk'

import logging

from schema import SchemaError, Schema
from tornado import gen

from tools_lib.gedis.gedis import Redis
from tools_lib.gtornado.escape import schema_utf8
from tools_lib.gtornado.web2 import BusinessReqHandler
from tools_lib.windchat import conf
from .utils import channel_utils
from .apis import account

redisc = Redis()

try:
    import ujson as json
except:
    import json


class SubscriberAppHandler(BusinessReqHandler):
    @gen.coroutine
    def prepare(self):
        # 优先使用客户端传来的client_id 可以减少请求次数
        self.client_id = self.request.headers.get("client-id", None)
        if not self.client_id:
            # 没有client_id的情况通常是客户端第一次请求
            yield self.get_subscriber_info_from_token()
            logging.info("Grabbed client_id[%s] because app don't pass the header 'client-id'" % self.client_id)
        logging.info("[client_id]:[%s]" % self.client_id)

    @gen.coroutine
    def get_subscriber_info_from_token(self):
        app_name = self.get_app_name()
        # 根据app-name判断去哪拿token对应的信息
        # TODO 如果需要修改对应关系,请去tools_lib.windchat.conf
        if conf.APP_NAME_2_TYPE[app_name]==conf.ACCOUNT_TYPE_MAN:
            self.origin_info = yield self.get_user_info_from_token()
            if not self.origin_info:
                self.resp_unauthorized()
                raise gen.Return()
            self.client_id = self.origin_info["clientId"]

        elif conf.APP_NAME_2_TYPE[app_name]==conf.ACCOUNT_TYPE_SHOP:
            self.origin_info = yield self.get_user_info_from_token()
            if not self.origin_info:
                self.resp_unauthorized()
                raise gen.Return()
            self.client_id = self.origin_info["clientId"]

        elif conf.APP_NAME_2_TYPE[app_name]==conf.ACCOUNT_TYPE_STAFF:
            logging.warn("An app trying windchat access as staff...")
            self.resp_unauthorized()
        else:
            logging.warn("An app with no app-name trying windchat access...")
            self.resp_unauthorized()


class ChannelsHandler(SubscriberAppHandler):
    def get(self):
        # TODO
        self.resp({})

    @gen.coroutine
    def patch(self):
        """
        @api {PATCH} /windchat/app/subscriber/channels 手动清空频道未读数
        @apiDescription 频道列表
        @apiName app_wc_channel_mark_read
        @apiGroup app_windchat
        @apiUse client_id_header

        @apiParam (json) {string} cli 频道id

        @apiParamExample {json} 请求示例
        {
            "cli": "dnghqrgruhg84tyu09higi"
        }

        @apiSuccessExample
            HTTP/1.1 201 Created
        """
        try:
            data = Schema({
                "cli": schema_utf8
            }).validate(self.get_body_args())
        except SchemaError:
            self.resp_error("failed when parsing schema.")
            return
        channel_utils.CP_mark_read(data["cli"], conf.CHANNEL_PRESENCE_ANY_CLIENT_ID, self.client_id)
        self.resp_created()


class AlertChannelHandler(SubscriberAppHandler):
    @gen.coroutine
    def get(self):
        """
        @api {GET} /windchat/app/subscriber/alert_channel 通知用频道的信息
        @apiDescription 频道列表
        @apiName app_wc_alert_channel
        @apiGroup app_windchat
        @apiUse client_id_header

        @apiSuccessExample
            HTTP/1.1 200 OK
            {
                "subscriber": {
                    "client_id": "weahgohrgprwg" // leancloud聊天ID
                }
                "alert_channel": {
                    "cli": 频道在leancloud的ID,
                    "name": 频道标题,
                    "unread": 未读数int
                }
            }
        """
        unread_count_last_message = channel_utils.CP_unread_count(
            conf.ALERT_CHANNEL_CURRENT,
            conf.CHANNEL_PRESENCE_ANY_CLIENT_ID,
            self.client_id
        )
        logging.info(unread_count_last_message)
        # _channels, _amount = yield channel.query_channel(cli_in=[conf.ALERT_CHANNEL_CURRENT])
        self.resp({
            "subscriber": {
                "client_id": self.client_id
            },
            "channels": {
                "cli": conf.ALERT_CHANNEL_CURRENT,
                "name": "", # _channels[0]["name"],
                "unread": unread_count_last_message[0]
            }
        })
