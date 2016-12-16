#! /usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals
from handlers import express

"""
    url的基本组成分为:
    模块名称:
    express, 用于nginx进行反向代理

    资源名称(资源类别):
    expr, expr为express的缩写, 表示运单这个资源, 如果两个都用全拼令人疑惑
    open这个类别下面主要是用来记录第三方的原始推单内容

    资源ID:
    如(\w+), 这里一般是运单号如00000000123, 也可能是ObjectId

    子资源:
    如qyjl, fh, 表示需要对订单中一些属性进行修改,
    从而映射到不同角色对运单的不同操作
"""
urls = []

# ==> 基本 <==
urls += [
    # [POST] 可下单,可送达
    (r"/express/can_be_served$", express.CanBeServed),
    # [POST] 一键呼叫
    (r'^/express/call$', express.OneKeyCall),
    # [POST] 一键呼叫列表/查询
    (r'^/express/call/search$', express.OneKeyCallPickle),
    # [GET] 该次呼叫中尚未完成收件的运单列表
    (r'^/express/call/expr_list$', express.ExprListInCall),

    # [PATCH] 对呼叫进行操作: 立即响应(抢呼叫)/ 关闭呼叫入口/ 加单(打印,定价)/ 生成收款码/ 收件
    (r'^/express/call/single/(\w+)$', express.OneKeyCallSingle),
    # [GET] 获取一个运单的详情, [PATCH]对一个运单进行操作
    (r"^/express/expr/single/(\w+)$", express.OneExpressHandler),

    # [PATCH] 派件员改价
    (r"^/express/expr/fee", express.Fee),
    # [PATCH] 派件员批量定价 todo del me
    (r"^/express/multi/pricing", express.Pricing),
    # [PATCH] 微信/支付宝 支付成功的首次通知
    (r"^/express/pay/call_back/notify_first_success", express.FirstSuccessPayNotification),

    # [POST] 代商户下单
    # (r'^/express/help_client$', express.HelpClient),
    # [PATCH] 领取运单
    # (r'^/express/assign_to_me', express.AssignToMe),
    # [POST] 填信息下单, [GET]搜索或者是查询运单列表
    (r"^/express/expr$", express.ExpressHandler),
    # [GET] 搜索或者是查询运单列表
    (r"^/express/expr/search$", express.PickleSearchHandler),
    # [PATCH] 派件员完善运单信息
    # (r"^/express/expr/(\w+)/receiver$", express.ReceiverHandler),
    # [PATCH] 商户余额支付
    (r"^/express/pay", express.PayExpress),
    # [GET] 聚合, 获取分类统计信息
    (r"^/express/aggregation$", express.AggregationHandler),
    # [GET] 聚合, 获取分类统计信息
    (r"^/express/aggregation/status$", express.AggregateStatusHandler),
    # [GET] 地址库: 模糊匹配发货地址信息、送达地址信息
    (r"^/express/client_address/fuzzy_search$", express.FuzzySearchAddressBaseHandler),
]

# ==> 站点-时刻-配送系人员 <==
urls += [
    # [GET] 站点信息列表
    ('^/express/node$', express.NodeGen),
    # [GET] 根据id获取人员签到列表
    ('^/express/schedule$', express.ScheduleHandler),
]
# ==> 站点-围栏-配送系人员 <==
urls += [
    # 围栏增[POST]删[DELETE]改[PATCH]简单查[GET]
    ('^/express/fence$', express.FenceHandler),
    # 判断坐标在哪个围栏内等复杂查询
    ('^/express/fence/complex_query$', express.FencePickle),
]
# ==> 数据导出 <==
urls += [
    # [POST]song: 导出运单
    (r"^/express/export/song$", express.ExpressExportHandler),
]

# ==> 奖惩, 结算, 其他数据 <==
# urls += [
#     (r"^/express/rewards/search$", rewards.PickleSearchHandler),
#     (r"^/express/rewards/aggregation$", rewards.AggregationHandler),
#     (r"^/express/settlement/search$", settlement.PickleSearchHandler),
#     (r"^/express/settlement/aggregation$", settlement.AggregationHandler),
#     (r"^/express/op_data$", data.OpDataHandler),
# ]
