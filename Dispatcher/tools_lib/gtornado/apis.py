# coding:utf-8


import json
import logging

from tornado.gen import coroutine, Return
from tornado.httpclient import HTTPRequest

from tools_lib.gtornado import async_requests
from tools_lib.gtornado.http_code import HTTP_200_OK
from tools_lib.host_info import IP_PORT_API
from tools_lib.pricing import pricing, DEFAULT_CATEGORY, FH_BASE, CATEGORIES

timeouts = {
    "connect_timeout": 0.5,
    "request_timeout": 2
}
wxpay_timeouts = {
    'connect_timeout': 5,
    'request_timeout': 10
}


@coroutine
def get_bind_man(id):
    # FIXME
    url = IP_PORT_API + "/deliveryman/outsource/get/man_list"
    resp = yield async_requests.get(url, {'id': id})
    ret = json.loads(resp.body)
    raise Return(ret)


@coroutine
def query_fence_manager(point_or_points_list):
    """
    传入一些坐标,返回这些坐标所在fence的全部联系人
    :param point_or_points_list: [
    {
        "lat":
        "lng":
    }, ...
    ]
    :return: list of manager info
    """
    url = IP_PORT_API + "/schedule/logic/fence/manager-filter"
    resp = yield async_requests.fetch(HTTPRequest(
        url,
        method="POST",
        body=json.dumps({
            "locs": point_or_points_list
        }),
        headers={"Content-Type": "application/json"},
        **timeouts
    ))
    logging.info(resp.body)
    raise Return(json.loads(resp.body)["content"])


@coroutine
def generate_number():
    """
    运单号生成器
    :return: number
    """
    url = IP_PORT_API + "/tracking_number/gen"
    resp = yield async_requests.fetch(HTTPRequest(
        url,
        method="GET",
        **timeouts
    ))
    num = json.loads(resp.body)
    raise Return(num["tracking_number"])


@coroutine
def shop_wxpay_code_url(shop_id, shop_name, shop_tel, cash):
    """
    由配送员生成给商户用微信APP扫码付款的二维码.
    {
        "shop": {
            "id": "57031774eed0934930609c53",
            "name": "霉霉",
            "tel": "132"
        },
        "cash": 0.01
    }
    """
    url = IP_PORT_API + '/shop/native/wx_pay'
    data = {
        "shop": {
            "id": shop_id,
            "name": shop_name,
            "tel": shop_tel
        },
        "cash": cash
    }
    resp_obj = yield async_requests.post(url=url, json=data, **wxpay_timeouts)
    if resp_obj.code == HTTP_200_OK:
        ret = json.loads(resp_obj.body)
        raise Return(ret)
    else:
        logging.error(resp_obj.body)


@coroutine
def shop_alipay_code_url(shop_id, shop_name, shop_tel, cash):
    """
    由配送员生成给商户用支付宝APP扫码付款的二维码.
    :param shop_id:
    :param shop_name:
    :param shop_tel:
    :param cash:
    :return:
    """
    url = IP_PORT_API + '/shop/native/alipay'
    data = {
        "shop": {
            "id": shop_id,
            "name": shop_name,
            "tel": shop_tel
        },
        "cash": cash
    }
    resp_obj = yield async_requests.post(url=url, json=data, **wxpay_timeouts)
    if resp_obj.code == HTTP_200_OK:
        ret = json.loads(resp_obj.body)
        raise Return(ret)
    else:
        logging.error(resp_obj.body)


@coroutine
def shop_pay(shop_id, cash):
    """
    扣款
    :param shop_id:
    :param cash:
    :return:
    """
    url = IP_PORT_API + "/shop/cash_flow"
    data = {
        "transact_type": "pay",
        "shop_id": shop_id,
        "cash": cash
    }
    response = yield async_requests.post(url=url, json=data)
    if response.code == HTTP_200_OK:
        raise Return(True)
    else:
        raise Return(False)


@coroutine
def shop_refund(shop_id, cash):
    """
    退款
    :param shop_id:
    :param cash:
    :return:
    """
    url = IP_PORT_API + "/shop/cash_flow"
    data = {
        "transact_type": "refund",
        "shop_id": shop_id,
        "cash": cash
    }
    response = yield async_requests.post(url=url, json=data)
    if response.code == HTTP_200_OK:
        raise Return(True)
    else:
        raise Return(False)


@coroutine
def shop_balance(shop_id):
    """
    查商户余额
    :param shop_id:
    :return:
    """
    if not shop_id:
        raise Return(0)

    url = IP_PORT_API + "/shop/flow_statistics/complex_query"
    data = {
        "filter_col": ["balance"],
        "query": {
            "op": "AND",
            "exprs": [
                {"shop_id": {"=": shop_id}}
            ]
        }
    }
    response = yield async_requests.post(url=url, json=data)
    balance = 0.0

    if response.code == HTTP_200_OK:
        ret = json.loads(response.body)
        if len(ret) == 1:
            balance = ret[0]

    raise Return(balance)


@coroutine
def multi_shop_balance(shop_id_list):
    """
    查一組商戶的餘額
    :param shop_id_list:
    :return:
    """
    if not shop_id_list:
        raise Return({})

    url = IP_PORT_API + "/shop/flow_statistics/complex_query"
    data = {
        'filter_col': ['balance', 'shop_id'],
        'query': {
            'op': 'AND',
            'exprs': [
                {'shop_id': {'in': shop_id_list}}
            ]
        }
    }
    response = yield async_requests.post(url=url, json=data)

    balances = {}
    if response.code == HTTP_200_OK:
        ret = json.loads(response.body)
        # 把返回列表变成形如{shop_id: balance}的字典
        for r in ret:
            balances[r['shop_id']] = r['balance']
        any_left = set(shop_id_list) - set(balances.keys())
        for s in any_left:
            balances[s] = 0.0
    raise Return(balances)


@coroutine
def get_fee(shop_id, category=DEFAULT_CATEGORY, **kwargs):
    """
    获取完整的商户定价
    :param shop_id:
    :param category:
    :param kwargs: 可选参数, 支持 volume=0/weight=0
    :return: {'fh': 13, 'fh_base':12, 'fh_extra': 1, 'msg': '0-1kg', 'category': '标准件'}
    失败返回 {}
    """
    # 0.1 庄兵和柳达配送费1分钱: 前两个是线上, 后两个是dev. 56cc0f9aeed0932e60a16966
    if shop_id in ('wdseTgDnsTQKKlwer46f6ivw', 'dada_prod',
                   '5773acbbb3a525019093119d', 'dada_dev'):
        fee = {"fh_base": 0.01, 'category': category}
    # 0.2 根据品类设置基础价格
    else:
        fh_base = CATEGORIES.get(category, FH_BASE)
        fee = {'fh_base': fh_base, 'category': category}

    # 1. 不管成功没有, 计算fh_extra
    fh_extra, msg, _max = pricing(volume=kwargs.get('volume', 0.0), weight=kwargs.get('weight', 0.0))
    fee['msg'] = msg
    fee['fh_extra'] = fh_extra

    # 2. 取到了该商户的定价, 计算改单总价, 并返回
    if fee and 'fh_base' in fee and fee['fh_base']:
        fee['fh'] = fee['fh_base'] + fee['fh_extra']
        raise Return(fee)
    if not fee:
        fh_base = CATEGORIES.get(category, 12)
        fee = {"fh": fh_base, "fh_base": fh_base, "fh_extra": 0, 'msg': '0-1kg', 'category': category}

    raise Return(fee)


if __name__ == '__main__':
    from tornado.ioloop import IOLoop
    from functools import partial

    f = partial(get_fee, '5773acbbb3a525019093119d')
    print(("shop_charge: %s" % IOLoop.current().run_sync(f)))
