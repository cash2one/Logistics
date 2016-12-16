#coding=utf-8
__author__ = 'kk'

from handlers import callback, api, answerer, subscriber, manager, util, conversation


urls = [
    # =============================> 基于频道的风信 <================================
    # [POST]给leancloud的回调接口
    (r'^/windchat/open/leancloud/channel/callback$', callback.LeancloudChannelMessageCallback),
    # [POST]频道消息发送接口 [仅允许api以外的服务器使用]
    (r'^/windchat/open/message/channel$', api.ChannelMsgDeliveringHandler),

    # [POST] 给所有人群发频道消息
    (r'^/windchat/util/channel/message/all$', util.SendChannelMsgToAllHandler),
    (r'^/windchat/util/channel/message/by_tel$', util.SendChannelMsgByTelHandler),

    # 管理者
    # (r'^/windchat/fe/manager/channels$', manager.channels),
    # (r'^/windchat/fe/manager/channel$', manager.channel),
    # (r'^/windchat/fe/manager/channel/(\w+)$', manager.channel),

    # 客服
    (r'^/windchat/fe/answerer/channel/ws$', answerer.AnswererWS),

    # 订阅者
    # [GET]查看绑定的频道列表(not available) [PATCH]手动清空频道未读数
    (r'^/windchat/app/subscriber/channels$', subscriber.ChannelsHandler),
    # [GET]获取通知频道的简短信息
    # TODO 05-09: 此频道用于通知以及对话用, 频道信息 hard-coded, 见tools_lib.windchat.conf
    (r'^/windchat/app/subscriber/alert_channel$', subscriber.AlertChannelHandler),
]

urls += [
    # =============================> 点对点风信 <================================
    # 点对点未读数 GET获取未读数 POST未读数增加 DELETE未读数清空
    # (r'^/windchat/app/conversation/unread$', subscriber.AlertChannelHandler),
    (r'^/windchat/app/conversation/get$', conversation.ConversationHandler),
]