#coding=utf-8
__author__ = 'kk'

import traceback
from logging import info, debug, warn, error
from models import post_task, post


def generate_post_url(post_obj, raw_url=True, force_using_local=False):
    """
    制作一个稿件的url
    :param post_obj: 一个dict包含alternative_url, id
    :param force_using_local: 强行使用稿件本身的URL而非alternative_url
    :return: string
    """
    alternative_url = post_obj.get("alternative_url", None)
    post_obj_id = post_obj.get("id", "")
    if not post_obj_id:
        raise Exception("bad post with no id.")
    if alternative_url:
        return alternative_url

    # 注意:这里的URL格式要与urls.py中的一样
    return "http://api.gomrwind.com:5000/windchat/app/post/(\w+)/raw" % post_obj_id


# TODO cache
def pack_important_post_for_channel_bottom(client_id, cli):
    """
    为频道底部的重要公告做包装
    """
    important_notices = post_task.query_post_task(
        post_type_in=[post_task.POST_TYPE_IMPORTANT_NOTICE],
        receivers_in=[client_id],
        cli_in=[cli],
        ret_more=True,
        page=1,
        count=1
    )
    if important_notices:
        important_notices = important_notices[0]
        return {
            "title": important_notices["post_obj"]["title"],
            "url": generate_post_url(important_notices)
        }
    else:
        return {
            # no important notice
            "title": "[无]",
            "url": ""
        }


# TODO cache
def pack_sticky_post_for_channel_bottom(client_id, cli):
    """
    为频道底部的置顶新闻做包装
    """
    sticky_posts = post_task.query_post_task(
        post_type_in=[post_task.POST_TYPE_NEWS],
        receivers_in=[client_id],
        cli_in=[cli],
        ret_more=True,
        sticky=True
    )
    return [
        {
            "title": i["post_obj"]["title"],
            "url": generate_post_url(i)
        } for i in sticky_posts
    ]
