#coding=utf-8
__author__ = 'kk'

import platform
import traceback

import tornadoredis

import apis.account
import apis.profile
from schema import Schema, SchemaError, Optional
from tools_lib.common_util.archived.pagination import paginator
from tools_lib.gedis.gedis import Redis, REDIS_SERVERS
from tools_lib.gtornado.escape import schema_utf8, schema_int
from tools_lib.gtornado.http_code import is_success
from tools_lib.gtornado.web2 import CommandWSHandler
from tools_lib.leancloud import sdk, credentials
from tools_lib.windchat import conf
from tornado import gen
from utils import channel_utils, answerer_utils, message_utils

redisc = Redis()

try:
    import ujson as json
except:
    import json

# redis configuration
redis_conf = REDIS_SERVERS.get(platform.node())
redis_conf["selected_db"] = redis_conf["db"]
redis_conf.pop("db")


REQ_VERIFY_TOKEN = "verify-token" # 验证token
REQ_CHANNEL_LIST = "channel-list" # 获取频道列表
REQ_SUBSCRIBER_LIST = "subscriber-list" # 获取某个频道订阅者
REQ_SUBSCRIBER_MESSAGE_HISTORY = "subscriber-message-history" # 获取某个订阅者的消息历史
REQ_SEND_MESSAGE = "send-message" # 发送消息

REQ_NEW_MESSAGE = "new-message"
REQ_CHANNEL_UPDATED = "channel-updated"


class AnswererWS(CommandWSHandler):
    """
    @api {WebSocket} /windchat/fe/answerer/channel/ws 客服用的WebSocket
    @apiDescription 前端客服使用的ws
    @apiName fe_wc_answerer_ws
    @apiGroup fe_windchat

    @apiParamExample 结构
    {
        "command": "token"              // 命令名
        "command_id": ""                // 命令唯一标识,会在处理方处理之后返回,用于确认命令已经执行完毕(可选)
        "content": {...}                // 内容
    }

    @apiParam (command) {c2s} verify-token 验证token
    @apiParam (command) {c2s} channel-list 获取频道列表
    @apiParam (command) {c2s} subscriber-list 获取某个频道订阅者
    @apiParam (command) {c2s} subscriber-message-history 获取某个订阅者的消息历史
    @apiParam (command) {c2s} send-message 发送消息

    @apiParam (command) {s2c} new-message 新消息推送
    @apiParam (command) {s2c} channel-updated 频道更新

    @apiParamExample client-to-server示例
    req: {
        "command": "verify-token"
        "command_id": "qqqazxswedc"
        "content": { // 请求内容
            "token": "token jfagdFH2409PGHOBSbvoiwiohoifbsovbsp"
        }
    }

    resp: {
        "command": "verify-token"
        "command_id": "qqqazxswedc"
        "content": { // 响应内容
            "status": 1 // 表示验证成功
        }
    }

    @apiParamExample server-to-client示例
    {
        "command": "new-message"
        "command_id": "qqqazxswedc"
        "content": { // 请求内容
            "message": "蛤蛤",
            "message_type": 1
        }
    }


    @apiParamExample 各command的content文档

    // verify-token 验证token ===============================
    req: {
        "token": "token ncujabgfiwrbowbriogwegbweoi"
    }

    resp: {
        "status": false错误   true成功,
        "staff_info": {
            "talker_name": "黄硬杰",
            "talker_avatar": "http://",
            "talker_id": 123,
            "talker_type": "staff",
            "client_id": "",
        }
    }

    // channel-list 获取频道列表 ==============================
    // >>>>>>>>> 此命令暂不用 <<<<<<<<<
    req: {}

    resp: [
        {channel-info}, ...
    ]

    // subscriber-list 获取某个频道订阅者 ======================
    req: {
        "cli": "频道 id" // 此参数暂时不用
        "page": 页码, 缺省1
        "count": 每页, 缺省20
    }

    resp: [
        {channel-info}, ...
    ]

    // subscriber-message-history 获取某个订阅者的消息历史 =======
    req: {
        "client_id": "qazxsw123edc" // 订阅者的client_id
        "limit": 50 // 返回数,默认50
        "msgid": "fbeiwp8t80321" // 起始消息ID
        "max_ts": 789320 // 起始时间戳
    }

    resp: [
        {
            "msg_id": "T7FbKJ6fStG1As6UcrHguw", // 本条消息的ID
            "cli": "kdsjgoapnfp" // 频道cli
            "from": {
                "name": "客服",
                "avatar": "http://imkk.me/a.png"
            }
            "timestamp": 1457604009478,
            "from-ip":   "202.117.15.217",
            "data": {...}
        }, ...
    ]

    // send-message 发送消息 ==================================
    req: {
        "message": {...} // 消息内容,具体参考消息格式
    }

    resp: {
        "status": true成功送达 false失败
    }

    // new-message 新消息推送 =================================
    req: [
        {message}, ... // 具体参见消息格式定义
        在消息格式的基础上新加{
            "client_id": "风信 id",
            "unread_count": 未读数,
            "last_message": 最后一条消息的缩略
        }
    ]

    // channel-updated 新频道推送 ============================
    // >>>>>>>>> 此命令暂不用 <<<<<<<<<
    req: [
        // 频道可能是新创建的,也可能是已有的频道收到了新的未读消息\修改图标\修改名称等等
        {channel-info}, ...
    ]

    // subscriber-updated 新订阅者推送 ============================
    // >>>>>>>>> 此命令暂不用 <<<<<<<<<
    req: [
        // 订阅者可能是新创建的,也可能是已有的订阅者收到了新的未读消息
        {channel-info}, ...
    ]


    @apiParamExample {json} 对象结构
    {channel-info} - 频道信息
    {
        "client_id": "" // 订阅者在leancloud的ID,
        "profile": { # 个人信息
            "talker_id": "" // 订阅者本身的ID,
            "talker_type": "账户类型",
            "talker_name": "" // 显示名
            "talker_avatar": "http://imkk.me/123.png" // 显示头像
        },
        "unread": "0" 未读数, 如果为"MU"则表示是标记未读
        "last_message": 上一条消息的摘要
    }

    """
    def __init__(self, *args, **kwargs):
        super(AnswererWS, self).__init__(*args, **kwargs)
        self.status = {
            "cli": conf.ALERT_CHANNEL_CURRENT,      # FIXME 当前只有一个频道
            "client_id": None,                      # 当前停留的订阅者 client_id
            "displayed_client_ids": {
                # cli: [已经展示出去的收听者client_id, ...]
            },
            "token": None,                          # 登陆用的 token
            "authenticated": False,                 # 是否认证通过
            "answerer_info": {                      # 当前登录的客服的信息
                "client_id": None
            }
        }
        self.status["displayed_client_ids"][conf.ALERT_CHANNEL_CURRENT] = set() # FIXME
        # sdk
        self.rtm = sdk.AsyncRtm(**credentials.credentials)
        # 开启监听
        self.listen()

    def check_origin(self, origin): return True

    @gen.engine
    def listen(self):
        """
        initializing the ws
        """
        self.info("New answerer opened window for channel chatting...")
        # 'tredisc' stands for tornado-redis-client
        self.tredisc = tornadoredis.Client(**redis_conf)
        self.tredisc.connect()
        yield gen.Task(self.tredisc.subscribe, conf.TREDIS_CHANNEL_CURRENT)
        self.tredisc.listen(self.on_tredis_message)

    def on_tredis_message(self, msg):
        """
        response redis channel for new messages from apps.
        """
        if msg.kind=='message':
            data = json.loads(msg.body)
            try:
                for i in data:
                    if i["cli"]==self.status["cli"]:
                        self.send(REQ_NEW_MESSAGE, content=[i["message"]])

            except:
                self.error("Error occurred when executing message from tredisc.")
                self.error(traceback.format_exc())
                self.error("Data:")
                self.error(data)

        elif msg.kind=='disconnect':
            self.critical("Redis server is DOWN!")

    @gen.coroutine
    def cmd_verify_token(self, command_id, content):
        """
        验证 answerer 的 token
        """
        try:
            content = Schema({
                "token": schema_utf8
            }).validate(content)
        except SchemaError:
            self.send(REQ_VERIFY_TOKEN, command_id, "bad content structure.")
            return
        staff_info = yield apis.profile.staff_verify_token(content["token"])
        if staff_info:
            self.status["token"] = content["token"]
            self.status["authenticated"] = True
            self.status["answerer_info"] = answerer_utils.pack_staff_profile(staff_info)
            # account_info = yield apis.account.query_account(account={
            #     "account_id": staff_info["staffNum"],
            #     "account_type": conf.ACCOUNT_TYPE_STAFF
            # })
            # self.status["answerer_info"]["client_id"] = account_info[0] # append a new key containing client_id
            self.status["answerer_info"]["client_id"] = conf.SYSTEM_ANSWERER_CLIENT_ID
            self.info("Answerer with token [%s] authenticated." % self.status["token"])
            self.send(REQ_VERIFY_TOKEN, command_id, {
                "status": True,
                "staff_info": self.status["answerer_info"]
            })
        else:
            self.send(REQ_VERIFY_TOKEN, command_id, {
                "status": False
            })

    @gen.coroutine
    def cmd_channel_list(self, command_id, content):
        """
        获取频道列表
        """
        if not self.status["authenticated"]:
            self.send(REQ_CHANNEL_LIST, command_id, "not permitted.")
            return
        # TODO

    @gen.coroutine
    def cmd_subscriber_list(self, command_id, content):
        """
        某个频道的订阅者列表
        """
        if not self.status["authenticated"]:
            self.send(REQ_SUBSCRIBER_LIST, command_id, "not permitted.")
            raise gen.Return()
        try:
            content = Schema({
                Optional("cli", default=conf.ALERT_CHANNEL_CURRENT): schema_utf8, # FIXME 暂时只有一个频道
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
            }).validate(content)
        except SchemaError:
            self.send(REQ_SUBSCRIBER_LIST, command_id, "bad content structure.")
            raise gen.Return()

        if content["page"]==1:
            # 如果请求的是第一页,表示认为频道订阅人列表已经重新刷新了
            self.status["displayed_client_ids"][self.status["cli"]] = set()

        # FIXME 暂时的解决方案
        # STEP I
        # 获取顺序排好的全部 client_id
        sorted_client_ids = channel_utils.CP_freshness(self.status["cli"], conf.CHANNEL_TALKER_ANSWERER)
        all_client_ids = yield apis.account.query_account(full_resp=False)
        all_client_ids_sorted_and_unsorted = sorted_client_ids + list(set(all_client_ids).difference(sorted_client_ids))
        # self.info(all_client_ids_sorted_and_unsorted)

        # STEP II
        # 分页
        _ret, _ret1, _ret_2 = paginator(
            None,
            all_client_ids_sorted_and_unsorted,
            lambda x:x.id,
            page=content["page"],
            count=content["count"]
        )
        # 加入已推出缓存
        _ret = list(set(_ret).difference(self.status["displayed_client_ids"][self.status["cli"]]))
        self.status["displayed_client_ids"][self.status["cli"]].update(_ret)

        # STEP III
        # 按照 sorted_client_ids 的顺序获取未读数和最后一条消息
        unread_last_message_tuple_list = [channel_utils.CP_unread_count(
            cli=self.status["cli"],
            f=i,
            t=conf.CHANNEL_PRESENCE_ANY_CLIENT_ID
        ) for i in _ret]

        # STEP IV
        # 获取被分页的人的个人信息
        profiles_man = yield apis.profile.get_all_man()
        profiles_shop = yield apis.profile.get_all_shop()
        client_id_account_dict_list_man = yield apis.account.query_account(
            account=[{"account_type": conf.ACCOUNT_TYPE_MAN, "account_id":i["id"]} for i in profiles_man],
            full_resp=True
        )
        # self.info(len(client_id_account_dict_list_man))
        client_id_account_dict_list_shop = yield apis.account.query_account(
            account=[{"account_type": conf.ACCOUNT_TYPE_SHOP, "account_id":i["id"]} for i in profiles_shop],
            full_resp=True
        )
        # self.info(len(client_id_account_dict_list_shop))
        client_id_account_dict_list = client_id_account_dict_list_man + client_id_account_dict_list_shop
        # self.info(client_id_account_dict_list)
        client_id_account_dict_dict = {i["account_id"]: i for i in client_id_account_dict_list}
        profiles_with_client_id = []
        for i in profiles_man:
            d = client_id_account_dict_dict.get(i["id"])
            if d:
                profiles_with_client_id.append(dict(i.items() + d.items()))
        for i in profiles_shop:
            d = client_id_account_dict_dict.get(i["id"])
            if d:
                profiles_with_client_id.append(dict(i.items() + d.items()))
        # self.info(len(profiles_with_client_id))
        profiles_dict_with_client_id_as_key = {i["client_id"]: i for i in profiles_with_client_id}

        # self.info(_ret)
        # self.info(profiles_dict_with_client_id_as_key)
        # STEP V
        ret = answerer_utils.pack_man_profile(_ret, unread_last_message_tuple_list, profiles_dict_with_client_id_as_key)

        self.send(REQ_SUBSCRIBER_LIST, command_id, ret)


    @gen.coroutine
    def cmd_subscriber_message_history(self, command_id, content):
        """
        某个订阅者的聊天历史
        """
        if not self.status["authenticated"]:
            self.send(REQ_SUBSCRIBER_MESSAGE_HISTORY, command_id, "not permitted.")
            raise gen.Return()
        try:
            content = Schema({
                Optional("client_id", default=None): schema_utf8,
                Optional("limit", default=20): schema_int,
                Optional("msgid"): schema_utf8,
                Optional("max_ts"): schema_int
            }).validate(content)
        except SchemaError:
            self.send(REQ_SUBSCRIBER_MESSAGE_HISTORY, command_id, "bad content structure.")
            raise gen.Return()
        if not self.status["client_id"] and not content["client_id"]:
            self.send(REQ_SUBSCRIBER_MESSAGE_HISTORY, command_id, "Currently no client_id, please offer a client_id.")
            raise gen.Return()
        self.status["client_id"] = content.pop("client_id")
        resp = yield self.rtm.conversation_history_sys(self.status["cli"], self.status["client_id"], **content)
        if is_success(resp.code):
            channel_utils.CP_mark_read(
                self.status["cli"],
                f=self.status["client_id"],
                t=conf.CHANNEL_PRESENCE_ANY_CLIENT_ID
            )
            ret = yield answerer_utils.pack_leancloud_chat_history(json.loads(resp.body), self.status["cli"])
            self.send(
                REQ_SUBSCRIBER_MESSAGE_HISTORY,
                command_id,
                ret
            )

        else:
            self.send(REQ_SUBSCRIBER_MESSAGE_HISTORY, command_id, json.loads(resp.body))

    @gen.coroutine
    def cmd_send_message(self, command_id, content):
        """
        前端发来消息
        """
        if not self.status["authenticated"]:
            self.send(REQ_SEND_MESSAGE, command_id, "not permitted.")
            return
        try:
            content = Schema({
                "message": object
            }).validate(content)
        except SchemaError:
            self.send(REQ_SEND_MESSAGE, command_id, "bad content structure.")
            return
        if not self.status["client_id"]:
            self.send(REQ_SEND_MESSAGE, command_id, "No client_id figured.")
            return
        resp = yield self.rtm.send_message(
            from_peer=conf.SYSTEM_ANSWERER_CLIENT_ID,
            to_peers=[self.status["client_id"]],
            message=json.dumps(content["message"], ensure_ascii=False),
            conv_id=self.status["cli"],
        )
        if is_success(resp.code):
            self.send(REQ_SEND_MESSAGE, command_id, {
                "status": True
            })
            channel_utils.CP_unread_increase(
                self.status["cli"],
                f=self.status["answerer_info"]["client_id"],
                t=self.status["client_id"],
                last_message=message_utils.pack_message_summary(content["message"])
            )
            redisc.publish(conf.TREDIS_CHANNEL_CURRENT, {
                "cli": self.status["cli"],
                "message": content["message"],
                "from": self.status["answerer_info"]["client_id"]
            })
        else:
            self.send(REQ_SEND_MESSAGE, command_id, {
                "status": False
            })

    def on_close(self):
        self.tredisc.disconnect()