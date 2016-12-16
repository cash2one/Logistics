#coding=utf-8
__author__ = 'kk'

import requests

from tools_lib.windchat import http_utils
from tools_lib.windchat import conf, http_utils

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

def query_post_task(
        page=1,
        count=10,
        status_in=None,
        cli_in=None,
        sticky=None,
        receivers_in=None,
        post_type_in=None,
        ret_more=False
):
    """
    稿件任务查询
    :param page:
    :param count:
    :param status_in: 状态列表
    :param cli_in: 频道CLI列表
    :param sticky: 是否置顶过滤
    :param receivers_in: 接受者client_ID列表
    :param post_type_in: 稿件类别列表
    :param ret_more: 返回更多稿件信息?默认否
    :return:
    """
    url = conf.WC_BL_PREFIX + "/windchat/bl/post_task"

    if not status_in:
        status_in = []

    if not cli_in:
        cli_in = []

    if not sticky:
        sticky = ""
    else:
        sticky = http_utils.bool_vs_query_string(sticky)

    if not receivers_in:
        receivers_in = []

    if not post_type_in:
        post_type_in = []

    resp = requests.get(url,params={
        "page": page,
        "count": count,
        "status_in": http_utils.list_to_dot_string(status_in),
        "cli_in": http_utils.list_to_dot_string(cli_in),
        "sticky": sticky,
        "receivers_in": http_utils.list_to_dot_string(receivers_in),
        "post_type_in": http_utils.list_to_dot_string(post_type_in),
        "ret_more": http_utils.bool_vs_query_string(ret_more)
    })
    return resp.json()["content"]


# ============================== 不缓存 ==============================

def create_post_task(**kwargs):
    """
    创建稿件发布任务
    :param kwargs:
    :return:
    """
    url = conf.WC_BL_PREFIX + "/windchat/bl/post_task"
    # yield async_client.fetch(HTTPRequest(url, method="POST", body=json.dumps(kwargs)))


def delete_post_task(task_id):
    """
    删除稿件发布任务
    :param task_id: 任务ID
    :return:
    """
    url = conf.WC_BL_PREFIX + "/windchat/bl/post_task/%s" % task_id
    # yield async_client.fetch(HTTPRequest(url, method="DELETE"))
