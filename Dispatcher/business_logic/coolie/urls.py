# coding: utf-8
from __future__ import unicode_literals

from handlers import evaluate, wechat


# 评价
urls = [
    # [POST] 发货端、收货折评价
    (r'^/coolie/evaluate$', evaluate.EvaluateHandler),
]

# 微信公众号接口
urls += [
    # [POST] 公众号 URL
    (r'^/coolie/wechat/event_handler$', wechat.WeChatEventHandler)
]
