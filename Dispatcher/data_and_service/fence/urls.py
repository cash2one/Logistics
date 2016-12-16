# coding=utf-8
__author__ = 'kk'

from handlers import fence

# 请严格按照顺序来, 不然正则匹配会出错

urls = [
    # 判断坐标在哪些栅栏内
    (r'^/schedule/logic/fence/point_cmp$', fence.FencePointCompareHandler),
    (r'^/schedule/logic/fence/point_inout$', fence.IfInsideFenceHandler),
    # 栅栏增删查改
    (r'^/schedule/logic/fence$', fence.FenceHandler),
    (r'^/schedule/logic/fence/(\w+)$', fence.OneFenceHandler),

    # 传入一些坐标,返回这些坐标所在fence的全部联系人
    (r'^/schedule/logic/fence/manager-filter$', fence.FenceManagerFilter),
]
