# coding=utf-8
__author__ = 'kk'

from handlers import fence

# 栅栏
urls = [
    # 判断坐标在哪些栅栏内
    (r'^/schedule/fe/fence/point_cmp$', fence.FencePointCompareHandler),
    (r'^/schedule/fe/fence/point_inout$', fence.IfInsideFenceHandler),

    # [GET] 查围栏的管理员
    (r'^/schedule/app/fence/manager$', fence.ManagerHandler),

    # 栅栏增删查改
    (r'^/schedule/fe/fence$', fence.FenceHandler),
    (r'^/schedule/fe/fence/(\w+)$', fence.FenceHandler),
]
