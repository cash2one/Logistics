# coding: utf-8
from __future__ import unicode_literals
import json

from settings import DAS_API_HOST
from tornado import gen

from tools_lib.gtornado import async_requests
from tools_lib.gtornado.http_code import HTTP_200_OK
from models import Fence


@gen.coroutine
def api_gen_number():
    url = DAS_API_HOST + "/tracking_number/gen"
    res = yield async_requests.get(url=url)
    if res.code != HTTP_200_OK:
        raise gen.Return(None)
    else:
        raise gen.Return(json.loads(res.body)['tracking_number'])


# === 查询点落入的围栏 ===
def query_fence_point_within(point_lng_lat):
    """
    查找一个点落入的围栏(有多个则取第一个,无则返回x)
    :param point_lng_lat:
    :return: {"id": "", "name": "", "node": {id, name, loc{lng,lat,address}}}
    """
    fence = Fence.objects(node__id__exists=True, points__geo_intersects=point_lng_lat).first()
    if fence:
        node = fence.node
        node.pop('color', None)
        return {
            "id": str(fence.id),
            "name": fence.name,
            "node": node
        }
    return {
        "id": "x",
        "name": "___",
        "node": {}
    }
