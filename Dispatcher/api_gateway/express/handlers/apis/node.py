# coding:utf-8
from __future__ import unicode_literals
import json
import logging
from tornado.httpclient import HTTPRequest
from tornado.httputil import url_concat
from tornado import gen

from tools_lib.gtornado import async_requests
import settings
from config import timeouts


# === yun.123feng.com ===
# == 站点列表/查询
def redirect_node_simple_query(query, **kwargs):
    url = settings.BL_DAS_API_PREFIX + '/express/node'
    if query:
        kwargs.update(query)
    url = url_concat(url, kwargs)
    return HTTPRequest(
        url,
        method='GET',
        **timeouts
    )


# == 站点创建
def redirect_create_node(node_name, loc):
    url = settings.BL_DAS_API_PREFIX + '/express/node'
    body = {
        'name': node_name,
        'loc': loc,
        'time_table': []
    }
    return HTTPRequest(
        url,
        method='POST',
        body=json.dumps(body),
        headers={'Content-Type': 'applications/json'},
        **timeouts
    )


# == 站点名,地址修改/添加时刻(与人)/删除时刻(与人)/修改时刻(与人)
def redirect_modify_node(query, **kwargs):
    url = settings.BL_DAS_API_PREFIX + '/express/node'
    body = {
        'Q': query,
    }
    body.update(kwargs)
    return HTTPRequest(
        url,
        method='PATCH',
        body=json.dumps(body),
        headers={'Content-Type': 'applications/json'},
        **timeouts
    )


# == 站点删除: 做sanity check, 有绑定的围栏、人员时刻表时, 不允许删除
def redirect_delete_node(node_id):
    url = settings.BL_DAS_API_PREFIX + '/express/node'
    url = url_concat(url, {'id': node_id})
    return HTTPRequest(
        url,
        method='DELETE',
        **timeouts
    )


# == 围栏: 简单查询
def redirect_get_fence(**kwargs):
    url = settings.BL_DAS_API_PREFIX + '/express/fence'
    url = url_concat(url, kwargs)
    return HTTPRequest(
        url,
        method="GET",
        **timeouts
    )


# == 围栏: 创建
def redirect_post_fence(obj):
    url = settings.BL_DAS_API_PREFIX + '/express/fence'
    return HTTPRequest(
        url,
        method="POST",
        body=json.dumps(obj),
        headers={'Content-Type': 'applications/json'},
        **timeouts
    )


# == 围栏: 删除
def redirect_delete_fence(query):
    url = settings.BL_DAS_API_PREFIX + '/express/fence'
    url = url_concat(url, query)
    return HTTPRequest(
        url,
        method="DELETE",
        headers={'Content-Type': 'applications/json'},
        **timeouts
    )


# == 围栏: 修改
def redirect_patch_fence(query, **kwargs):
    url = settings.BL_DAS_API_PREFIX + '/express/fence'
    return HTTPRequest(
        url,
        method="PATCH",
        body=json.dumps(dict({"Q": query}.items() + kwargs.items())),
        headers={'Content-Type': 'applications/json'},
        **timeouts
    )


@gen.coroutine
def query_fence_point_within(point_lng_lat, need_mans=False):
    """
    查找一个点落入的围栏(有多个则取第一个,无则返回x)
    :param point_lng_lat:
    :param need_mans:
    :return: {"id": "", "name": "", "node": {id, name, loc{lng,lat,address}}}
    """
    # 设置默认返回
    ret = {
        "id": "x",
        "name": "___",
        "node": {}
    }
    if need_mans:
        ret['mans'] = []

    # 去查围栏
    resp_obj = yield async_requests.fetch(redirect_get_fence(
        lng=point_lng_lat[0],
        lat=point_lng_lat[1]
    ))

    # 如果成功, 覆盖默认返回
    if resp_obj.code == 200:
        fences = json.loads(resp_obj.body)
        if fences:
            fence = fences[0]
            try:
                node = {}
                for k in ('id', 'name', 'loc'):
                    node[k] = fence["node"][k]
                ret = {
                    "id": fence["id"],
                    "name": fence["name"],
                    "node": node,
                }
                if need_mans:
                    ret['mans'] = fence['mans']
            except Exception as e:
                logging.exception(e)

    # 不管成功失败, 都要返回
    raise gen.Return(ret)
