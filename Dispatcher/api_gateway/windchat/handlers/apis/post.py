#coding=utf-8
__author__ = 'kk'

import requests
from logging import info, debug, warn, error
from tornado.httpclient import HTTPRequest
from tools_lib.windchat import conf

try:
    import ujson as json
except:
    import json


# 稿件类型
POST_TYPE_NEWS = 1 # 普通新闻
POST_TYPE_IMPORTANT_NOTICE = 2 # 重要公告

# 稿件任务状态
POST_TASK_PENDING = 1
POST_TASK_SENDING = 2
POST_TASK_SENT = 3
POST_TASK_CANCELED = 4


# ============================== 可缓存 ==============================

def query_post(page=1, count=10, p_type=0, ret_level=0, cli_in=None):
    """
    查询稿件
    :param page: 页数
    :param count: 每页
    :param p_type: 稿件类型,integer
    :param ret_level: 返回类型,见DAS.models.Post
    :param cli_in: 频道cli列表
    :return:
    """
    url = conf.WC_BL_PREFIX + "/windchat/bl/posts"
    if not cli_in: cli_in = []
    resp = requests.get(url, params={
        "page": page,
        "count": count,
        "p_type": p_type,
        "ret_level": ret_level,
        "cli_in": ",".join(cli_in)
    })
    return resp.json()["content"]


def get_post(post_id):
    """
    获取稿件
    :param post_id:
    :return:
    """
    url = conf.WC_BL_PREFIX + "/windchat/bl/post/%s" % post_id
    resp = requests.get(url)
    return resp.json()["content"]

# ============================== 不缓存 ==============================

def delete_post(post_id):
    """
    删除稿件
    :param post_id:
    :return:
    """
    url = conf.WC_BL_PREFIX + "/windchat/bl/post/%s" % post_id
    # yield async_client.fetch(HTTPRequest(url, method="DELETE"))


def post_post(**kwargs):
    """
    创建稿件
    :param kwargs:
    :return:
    """
    url = conf.WC_BL_PREFIX + "/windchat/bl/post"
    # yield async_client.fetch(HTTPRequest(url, method="POST", body=json.dumps(kwargs)))


def patch_post(post_id, **kwargs):
    """
    修改稿件
    :param post_id:
    :param kwargs:
    :return:
    """
    url = conf.WC_BL_PREFIX + "/windchat/bl/post/%s" % post_id
    # yield async_client.fetch(HTTPRequest(url, method="PATCH", body=json.dumps(kwargs)))
