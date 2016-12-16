#coding=utf-8
__author__ = 'kk'

from handlers import channel, account

urls = [
    # 账户
    (r'^/windchat/das/account$', account.AccountHandler),
    (r'^/windchat/das/account/query$', account.AccountQueryHandler),

    # ====== 基于频道的聊天模式 ======
    # 频道批处理:基本
    (r'^/windchat/das/channels$', channel.BulkChannelHandler),
    # 单个频道
    (r'^/windchat/das/channel$', channel.ChannelHandler),
    (r'^/windchat/das/channel/(\w+)$', channel.ChannelHandler),

    # ====== 点对点模式 ======

]
