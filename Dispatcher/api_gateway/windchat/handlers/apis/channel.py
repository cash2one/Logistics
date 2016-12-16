#coding=utf-8
__author__ = 'kk'

from tornado import gen

from tools_lib.windchat import http_utils
from tools_lib.gtornado import async_requests
from tools_lib.windchat import conf, http_utils

try:
    import ujson as json
except:
    import json

# ============================== 可缓存 ==============================

@gen.coroutine
def query_channel(
        include_disabled=False,
        only_top=False,
        only_sticky=False,
        manager_in=None,
        poster_in=None,
        answerer_in=None,
        cli_in=None,
        page=1,
        count=10):
    """
    查询频道
    :param include_disabled:包含已禁用的频道
    :param only_top:仅置顶的频道
    :param only_sticky:仅推荐首页的频道
    :param manager_in:属于这些管理员
    :param poster_in:属于这些投稿者
    :param answerer_in:属于这些客服
    :param cli_in:指定频道ID列表
    :param page: 页
    :param count: 每页数
    :return:
    """
    url = conf.WC_DAS_PREFIX + "/windchat/das/channels"
    if not manager_in:
        manager_in = []
    if not poster_in:
        poster_in = []
    if not answerer_in:
        answerer_in = []
    if not cli_in:
        cli_in = []
    params = {
        "include_disabled": http_utils.bool_vs_query_string(include_disabled),
        "only_top": http_utils.bool_vs_query_string(only_top),
        "only_sticky": http_utils.bool_vs_query_string(only_sticky),

        "manager_id": http_utils.list_to_dot_string(manager_in),
        "poster_in": http_utils.list_to_dot_string(poster_in),
        "answerer_in": http_utils.list_to_dot_string(answerer_in),
        "cli_in": http_utils.list_to_dot_string(cli_in),

        "page": page,
        "count": count
    }
    resp = yield async_requests.get(url, params=params)
    raise gen.Return((json.loads(resp.body), resp.headers["X-Resource-Count"]))


@gen.coroutine
def get_channel(cli):
    """
    获取单个频道
    :param cli: 频道cli
    :return:
    """
    url = conf.WC_DAS_PREFIX + "/windchat/channel/%s" % cli
    resp = yield async_requests.get(url)
    raise gen.Return(json.loads(resp.body))


# ============================== 不缓存 ==============================

@gen.coroutine
def create_channel(**kwargs):
    """
    创建频道
    :param kwargs:
    :return:
    """
    url = conf.WC_DAS_PREFIX + "/windchat/channel"
    resp = yield async_requests.post(url, json=kwargs)
    raise gen.Return(json.loads(resp.body))


@gen.coroutine
def delete_channel(cli):
    """
    禁用频道
    :param cli: 频道cli
    :return:
    """
    url = conf.WC_DAS_PREFIX + "/windchat/channel/%s" % cli
    yield async_requests.delete(url)


@gen.coroutine
def patch_channel(cli, **kwargs):
    """
    修改频道
    :param cli: 频道cli
    :param kwargs:
    :return:
    """
    url = conf.WC_DAS_PREFIX + "/windchat/channel/%s" % cli
    resp = yield async_requests.patch(url, json=kwargs)
    raise gen.Return(json.loads(resp.body))
