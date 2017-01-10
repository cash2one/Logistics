# coding:utf-8


import logging
import traceback
from functools import wraps
from tornado import gen
from tools_lib.gtornado import async_requests
from tools_lib.java_host_info import JAVA_DATA_PREFIX
from tools_lib.gtornado import http_code


# 创建日志
@gen.coroutine
def log_create(isVal=None, type="",
               # 日志创建者
               creatorId="", creatorName="", creatorTel="", creatorRole="", createTime="",
               # 影响者
               effectorId="", effectorName="", effectorTel="", effectorRole="",
               # 运单信息
               orderId="", orderSum="", orderState=0, orderType="", orderAddress="", orderCreator="", orderLat=0.0,
               orderLng=0.0,
               # 客户信息
               shopAddress="", shopLat=0.0, shopLng=0.0, shopId="", shopName="", shopTel="",
               # 资金
               fondSum=0.0, fondType="",
               # 交通工具
               vehicleId="", vehicleMile="",
               # 软件版本
               softwareVersion="",
               # 地理信息
               locationAddress="", locationLat=0.0, locationLng=0.0,
               # 其他
               remark="", caseId="", caseType="", caseDetail="", amount=0,
               **kwargs):
    """新增参数请加到上面并归类, 未加入的参数会被忽略(warning提示)"""
    if kwargs:
        logging.warn("Got unprocessed params: " + repr(kwargs))
    url = JAVA_DATA_PREFIX + "/WindCloud/log/create"

    d = dict(
        isVal=isVal,  # 是否有效
        type=type,  # 日志类型

        # 日志创建者
        creatorId=creatorId,
        creatorName=creatorName,
        creatorTel=creatorTel,
        creatorRole=creatorRole,
        createTime=createTime,  # 日志创建时间

        # 影响者
        effectorId=effectorId,
        effectorName=effectorName,
        effectorTel=effectorTel,
        effectorRole=effectorRole,

        # 运单信息
        orderId=orderId,
        orderSum=orderSum,
        orderState=orderState,  # 运单状态
        orderType=orderType,
        orderAddress=orderAddress,
        orderCreator=orderCreator,
        orderLat=orderLat,
        orderLng=orderLng,

        # 客户信息
        shopAddress=shopAddress,
        shopLat=shopLat,
        shopLng=shopLng,
        shopId=shopId,
        shopName=shopName,
        shopTel=shopTel,

        # 资金
        fondSum=fondSum,  # 资金总数
        fondType=fondType,  # 资金类型

        # 交通工具
        vehicleId=vehicleId,  # 车辆牌号
        vehicleMile=vehicleMile,  # 里程数

        # 软件版本
        softwareVersion=softwareVersion,

        # 地理信息
        locationAddress=locationAddress,
        locationLat=locationLat,
        locationLng=locationLng,

        # 其他
        remark=remark,
        caseId=caseId,  # 事件 id
        caseType=caseType,  # 事件类型
        caseDetail=caseDetail,  # 事件详情
        amount=amount  # 数量
    )
    d = {i: d[i] for i in d if d[i]}
    logging.info("windlog.log_create: " + repr(d))
    resp = yield async_requests.post(url, json=d)
    if not resp:
        logging.warn("Got empty windlog resp")
    if not http_code.is_success(resp.code):
        logging.warn("Windlog failed with code %s" % resp.code)


if __name__ == '__main__':
    import arrow
    from tornado.ioloop import IOLoop
    from functools import partial

    args = dict(
        type=21001,
        shopId='5773acbbb3a525019093119d',
        createTime=arrow.utcnow().isoformat(),
        amount=1,
        locationLat=0.0,
        locationLng=0.0,
        caseId='578f13bd2d50c07466d30449'
    )
    f = partial(log_create, **args)
    log = IOLoop.current().run_sync(f)
    print(log)
