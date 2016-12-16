# coding=utf-8
__author__ = 'kk'
'''
风信相关配置

* 修改之前,请务必明确自己在做什么.
'''

import logging
import sys

# === HTTPRequest超时 ===
timeouts = {
    "connect_timeout": 0.5,
    "request_timeout": 2
}
logging.info("timeouts: %s" % timeouts)

# === 聊天账户类型 ===
# 聊天类型
ACCOUNT_TYPE_MAN = "man"  # 配送员\派件员\取件员\各种员
ACCOUNT_TYPE_SHOP = "shop"  # 商户\发货者
ACCOUNT_TYPE_STAFF = "staff"  # 公司员工
# 聊天类型列表
ACCOUNT_TYPES = [
    ACCOUNT_TYPE_MAN,
    ACCOUNT_TYPE_SHOP,
    ACCOUNT_TYPE_STAFF
]
logging.info("all account types: %s" % ACCOUNT_TYPES)

# === http请求的地址和端口配置 ===
import platform
from tools_lib.host_info import LOCALHOST_NODE, LOCALHOST_IP, \
    DEV_NODE, DEV_OUTER_IP, \
    PROD_API_NODE, PROD_BL_DAS_PORT, PROD_API_INNER_IP

current_node = platform.node()
if current_node in (LOCALHOST_NODE,):
    # DEV at localhost
    WC_DAS_PREFIX = "http://{hostip}:{port}".format(hostip=LOCALHOST_IP, port=PROD_BL_DAS_PORT)
    WC_BL_PREFIX = "http://{hostip}:{port}".format(hostip=LOCALHOST_IP, port=PROD_BL_DAS_PORT)
    DEBUG = True

elif current_node in (DEV_NODE,):
    # DEV at 209
    WC_DAS_PREFIX = "http://{hostip}:{port}".format(hostip=DEV_OUTER_IP, port=PROD_BL_DAS_PORT)
    WC_BL_PREFIX = "http://{hostip}:{port}".format(hostip=DEV_OUTER_IP, port=PROD_BL_DAS_PORT)
    DEBUG = True

elif current_node in (PROD_API_NODE,):
    # PROD at 69
    WC_DAS_PREFIX = "http://{hostip}:{port}".format(hostip=PROD_API_INNER_IP, port=PROD_BL_DAS_PORT)
    WC_BL_PREFIX = "http://{hostip}:{port}".format(hostip=PROD_API_INNER_IP, port=PROD_BL_DAS_PORT)
    DEBUG = False

else:
    raise Exception("windchat sdk: no configuration for this node: %s" % current_node)
logging.info("WC_DAS_PREFIX: %s, WC_BL_PREFIX: %s, DEBUG==%s" % (WC_DAS_PREFIX, WC_BL_PREFIX, DEBUG))

# === rabbit-mq的exchange ===
from tools_lib.common_util.rabbitmq_client import EXCHANGE_WINDCHAT4_0, EXCHANGE_WINDCHAT4_1

code_dir_to_mq_exchange = {
    "/root/MrWind-Dispatcher": EXCHANGE_WINDCHAT4_0,
    "/xvdb/MrWind-Dispatcher": EXCHANGE_WINDCHAT4_1
}
# 当前导入wc4的程序应当使用的exchange
try:
    # TODO sys.path的第一条必须为代码仓库的目录
    CURRENT_EXCHANGE = code_dir_to_mq_exchange[sys.path[0]]
except:
    # exceptions when debugging locally
    logging.warn("You're now using default windchat exchange")
    CURRENT_EXCHANGE = EXCHANGE_WINDCHAT4_0
logging.info("RabbitMQ exchange for windchat: " + CURRENT_EXCHANGE)

# === tornado redis 的 channel ===
TREDIS_CHANNEL_0 = "WC4-CHANNEL-0"
TREDIS_CHANNEL_1 = "WC4-CHANNEL-1"
code_dir_to_tredis_channel = {
    "/root/MrWind-Dispatcher": TREDIS_CHANNEL_0,
    "/xvdb/MrWind-Dispatcher": TREDIS_CHANNEL_1
}
# 当前导入wc4的程序应当使用的tredis channel
try:
    # TODO sys.path的第一条必须为代码仓库的目录
    TREDIS_CHANNEL_CURRENT = code_dir_to_tredis_channel[sys.path[0]]
except:
    # exceptions when debugging locally
    logging.warn("You're now using default windchat tornado-redis channel")
    TREDIS_CHANNEL_CURRENT = TREDIS_CHANNEL_0
logging.info("Tornado redis channel name for windchat: " + TREDIS_CHANNEL_CURRENT)

# === rabbit mq所在的服务器 ===
if DEBUG:
    MQ_HOST = DEV_OUTER_IP
else:
    MQ_HOST = LOCALHOST_IP  # Using locally, otherwise another account is needed
# TODO SEE:
# http://stackoverflow.com/questions/30223339/pika-exceptions-probableauthenticationerror-when-trying-to-send-message-to-remot
logging.info("RabbitMQ server: " + MQ_HOST)

# === 系统客服 ===
SYSTEM_ANSWERER_CLIENT_ID = "SYSTEM_ANSWERER"
SYSTEM_ANSWERER_NAME = "系统通知"
DEFAULT_ANSWERER_AVATAR = "http://7qn9s9.com2.z0.glb.qiniucdn.com/风信客服头像.png"
logging.info("System answerer client_id: " + SYSTEM_ANSWERER_CLIENT_ID)

# === 通知频道 ===
# FIXME HARD-CODED!!!
# TODO 必须和数据库同步!
# >>> DEV <<<
ALERT_CHANNEL_DEV = "573182e8df0eea006331284c"
# >>> PROD <<<
ALERT_CHANNEL_PROD = "573aec78df0eea005e6f33b7"
# >>> CURRENT <<<
ALERT_CHANNEL_CURRENT = ALERT_CHANNEL_DEV if DEBUG else ALERT_CHANNEL_PROD
logging.info("Alert channel id: " + ALERT_CHANNEL_CURRENT)

# === app-name 转成man shop staff信息 ===
# TODO 添加或者改变了 app 的 app-name 之后,记得修改这里!
APP_NAME_2_TYPE = {
    # App发货端
    "customer_b": ACCOUNT_TYPE_SHOP,
    # App区域经理端
    "area_manager": ACCOUNT_TYPE_MAN,
    # 收派端
    "parttime": ACCOUNT_TYPE_MAN,
    # 城际司机 环线司机
    "city_driver": ACCOUNT_TYPE_MAN,
}
logging.info("app-name to type mapping: ")
logging.info(APP_NAME_2_TYPE)

# === 消息类型 ===
MSG_TYPE_PLAIN_TEXT = 1  # 纯文本
MSG_TYPE_IMAGE = 2  # 单独图片
MSG_TYPE_DELIVERY_ALERT = 3  # 配送提醒
MSG_TYPE_ROUTINE_ALTERED_ALERT = 4  # 线路变更提醒
# 消息类型列表
MSG_TYPES = [
    MSG_TYPE_PLAIN_TEXT,
    MSG_TYPE_IMAGE,
    MSG_TYPE_DELIVERY_ALERT,
    MSG_TYPE_ROUTINE_ALTERED_ALERT
]
logging.info("All message type:")
logging.info(MSG_TYPES)

# === 频道发送风信的 type ===
MQ_TYPE_SEND_NOW = "SEND-NOW"
MQ_TYPE_SCHEDULE = "SCHEDULE"
MQ_TYPE_SCHEDULE_CANCEL = "SCHEDULE-CANCEL"

# === leancloud 回调带上的 token ===
LC_CALLBACK_TOKEN_DEV = "cb0d766c87f5f4bd2df6baf2482682fe"
LC_CALLBACK_TOKEN_PROD = "1a74ff559f8f0bd449f5b130fe9969f0"
LC_CALLBACK_TOKEN_CURRENT = LC_CALLBACK_TOKEN_DEV if DEBUG else LC_CALLBACK_TOKEN_PROD
logging.info("Leancloud callback token: " + LC_CALLBACK_TOKEN_CURRENT)

# === 消息未读\新鲜度\最后一条消息 ===
# 消息新鲜度排序
# 排序的 score 为time.time()
# 订阅者看到的频道新鲜度, 存放cli
CHANNEL_PRESENCE_FRESHNESS_TALKER_SUBSCRIBER = "WC4-CHANNEL-PRESENCE-FRESHNESS:{cli}:SUBSCRIBER-CLI"
# 客服看到的订阅者新鲜度, 存放client_id
CHANNEL_PRESENCE_FRESHNESS_TALKER_ANSWERER = "WC4-CHANNEL-PRESENCE-FRESHNESS:{cli}:ANSWERER-CLIENT-ID"
# 频道聊天角色
CHANNEL_TALKER_SUBSCRIBER = "SUBSCRIBER"  # 订阅者
CHANNEL_TALKER_ANSWERER = "ANSWERER"  # 客服
# 未读数 key 模板
CHANNEL_PRESENCE_UNREAD_TEMPLATE = "WC4-CHANNEL-PRESENCE:{cli}:{from_client_id}:{to_client_id}:UNREAD_COUNT"
# 标记未读
CHANNEL_PRESENCE_MARKED_UNREAD = "MU"  # for 'marked unread'
# 最后一条消息 key 模板
CHANNEL_PRESENCE_LAST_MESSAGE_TEMPLATE = "WC4-CHANNEL-PRESENCE:{cli}:{from_client_id}:{to_client_id}:LAST_MESSAGE"
# 任意client_id
CHANNEL_PRESENCE_ANY_CLIENT_ID = "*"

# ==== 消息未读 ====
# 未读数 key 模板
CONV_PRESENCE_UNREAD_TEMPLATE = "WC4-CONVERSATION-PRESENCE:{conv_id}:{from_client_id}:{to_client_id}:UNREAD_COUNT"

# === 频道订阅者\客服 ===
# FIXME 这块仍有待商榷
# 频道订阅者命名空间
CHANNEL_SUBSCRIBER_DOMAIN = "WC4-CHANNEL-SUBSCRIBER"
# 模板
CHANNEL_SUBSCRIBER_TEMPLATE = "%s:{cli}:{client_id}" % CHANNEL_SUBSCRIBER_DOMAIN
# 过滤任意
CHANNEL_SUBSCRIBER_FILTER_ANY = "*"

# === Java 服务前缀 ===
JAVA_SERVICE_PREFIX_DEV = "http://10.173.47.109:8080"
JAVA_SERVICE_PREFIX_PROD = "http://182.92.115.196:8080"
JAVA_SERVICE_PREFIX_CURRENT = JAVA_SERVICE_PREFIX_DEV if DEBUG else JAVA_SERVICE_PREFIX_PROD
logging.info("Java service prefix: " + JAVA_SERVICE_PREFIX_CURRENT)
