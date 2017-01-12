#coding=utf-8
__author__ = 'kk'
"""

维护频道风信的频道绑定\未读数\新鲜排名\最后一条消息

"""

import re
import time
import logging
from tools_lib.windchat import conf
from tools_lib.gedis.gedis import Redis

redisc = Redis()

try:
    import ujson as json
except:
    import json


# ==================== CP stands for channel presence ====================

def CP_unread_increase(cli, f, t, last_message="", n=1):
    """
    频道未读数增加,新鲜度刷新,更新最后一条消息
    :param cli:
    :param f: from_client_id
    :param t: to_client_id
    :param last_message:
    :param n:
    """
    # 保证消息是个文本
    if isinstance(last_message, (list, dict, tuple)):
        last_message = json.dumps(last_message, ensure_ascii=False)
    # execute commands through pipeline
    r_p_line = redisc.pipeline()
    # 分别更新客服看到的排名和订阅者看到的排名
    freshness_key_answerer = conf.CHANNEL_PRESENCE_FRESHNESS_TALKER_ANSWERER.format(cli=cli)
    freshness_key_subscriber = conf.CHANNEL_PRESENCE_FRESHNESS_TALKER_SUBSCRIBER.format(cli=cli)
    r_p_line.zadd(freshness_key_answerer, f, time.time())
    r_p_line.zadd(freshness_key_subscriber, cli, time.time())
    # 更新未读数和最后一条消息
    unread_key = conf.CHANNEL_PRESENCE_UNREAD_TEMPLATE.format(cli=cli,from_client_id=f, to_client_id=t)
    last_key = conf.CHANNEL_PRESENCE_LAST_MESSAGE_TEMPLATE.format(cli=cli,from_client_id=f, to_client_id=t)
    r_p_line.incrby(unread_key, n)
    r_p_line.set(last_key, last_message)
    # Execute now!
    r_p_line.execute()

def CP_mark_read(cli, f, t):
    """
    标记已读
    """
    unread_key = conf.CHANNEL_PRESENCE_UNREAD_TEMPLATE.format(cli=cli,from_client_id=f, to_client_id=t)
    redisc.set(unread_key, 0)

def CP_unread_count(cli, f, t, r_p_line=None):
    """
    未读数\最后一条消息
    :param cli:
    :param f:
    :param t:
    :return: (_unread_count, _last_message)
    """
    unread_key = conf.CHANNEL_PRESENCE_UNREAD_TEMPLATE.format(cli=cli,from_client_id=f, to_client_id=t)
    last_key = conf.CHANNEL_PRESENCE_LAST_MESSAGE_TEMPLATE.format(cli=cli,from_client_id=f, to_client_id=t)
    if r_p_line:
        r_p_line.get(unread_key)
        r_p_line.get(last_key)
    else:
        r_p_line = redisc.pipeline()
        r_p_line.get(unread_key)
        r_p_line.get(last_key)
        ret = r_p_line.execute()
        if ret[0]==None: ret[0] = 0
        if ret[1]==None: ret[1] = ""
        return int(ret[0]), ret[1]

def CP_bulk_unread_count(kwargs):
    """
    批量获得未读数\威后一条消息
    :param kwargs: CP_unread_count的参数
    :return: [(_unread_count, _last_message), ...]
    """
    r_p_line = redisc.pipeline()
    for i in kwargs:
        CP_unread_count(r_p_line=r_p_line, **i)
    resp = r_p_line.execute()
    resp.reverse()
    ret = []
    while resp:
        last_message = resp.pop()
        unread = resp.pop()
        if last_message==None: last_message = ""
        if unread==None: unread = 0
        ret.append((unread, last_message))
    return ret

def CP_freshness(cli, talker):
    """
    新鲜度排序
    :param cli:
    :param talker: 类型
    :return: client_id列表或者cli列表
    """
    if talker==conf.CHANNEL_TALKER_SUBSCRIBER:
        k = conf.CHANNEL_PRESENCE_FRESHNESS_TALKER_SUBSCRIBER.format(cli=cli)
    elif talker==conf.CHANNEL_TALKER_ANSWERER:
        k = conf.CHANNEL_PRESENCE_FRESHNESS_TALKER_ANSWERER.format(cli=cli)
    else:
        raise Exception("Bad talker.")
    return redisc.zrevrange(k, 0, -1)


# FIXME 这块仍有待商榷
class Subscriber(object):
    """
    维护频道订阅者
    """
    def __init__(self, redis_c, cli=conf.CHANNEL_SUBSCRIBER_FILTER_ANY, client_id=conf.CHANNEL_SUBSCRIBER_FILTER_ANY):
        if cli == client_id == conf.CHANNEL_SUBSCRIBER_FILTER_ANY:
            raise Exception("You just can't filter any to any!")

        self.redis_c = redis_c
        self.cli = cli
        self.client_id = client_id
        self.key = conf.CHANNEL_SUBSCRIBER_TEMPLATE.format(
            cli=cli,
            client_id=client_id
        )

    def check_relation(self):
        """
        检查两者之间是否已经绑定
        这种情况下所有参数都不可为FILTER_ANY
        :return: bool
        """
        return self.redis_c.exists(self.key)

    def bind(self, accessory_info="{}"):
        """
        绑定
        这种情况下所有参数都不可为FILTER_ANY
        """
        if not isinstance(accessory_info, str):
            accessory_info = json.dumps(accessory_info, ensure_ascii=False)
        self.redis_c.set(self.key, accessory_info)

    def channel_bulk_bind_subscribers(self, subscriber_client_ids):
        """
        给该频道批量绑定收听者
        这种情况下忽略client_id
        :param subscriber_client_ids: list
        :return:
        """
        if self.cli in (None, conf.CHANNEL_SUBSCRIBER_FILTER_ANY):
            raise Exception("cli is None or Filter_Any")
        for i in subscriber_client_ids:
            self.redis_c.set(conf.CHANNEL_SUBSCRIBER_TEMPLATE.format(
                cli=self.cli,
                client_id=i
            ), "{}")

    def unbind(self):
        """
        解绑
        这种情况下所有参数都不可为FILTER_ANY
        """
        self.redis_c.delete(self.key)

    def get_channel_subscribers(self):
        """
        获得频道全部收听者client_id列表
        """
        keys = self.redis_c.keys(self.key)
        re_tmpl = re.compile(conf.CHANNEL_SUBSCRIBER_TEMPLATE.format(
            cli=self.cli,
            client_id=r"(.*?)"
        ))

        ret = []
        for i in keys:
            matched_params = re_tmpl.findall(i)
            if matched_params:
                ret.append(matched_params[0])
        return ret

    def get_subscriber_channels(self):
        """
        获得此人全部频道
        :return:
        """
        keys = self.redis_c.keys(self.key)
        re_tmpl = re.compile(conf.CHANNEL_SUBSCRIBER_TEMPLATE.format(
            cli=r"(.*?)",
            client_id=self.client_id
        ))

        ret = []
        for i in keys:
            matched_params = re_tmpl.findall(i)
            if matched_params:
                ret.append(matched_params[0])
        return ret


# ========= > channel subscriber shortcuts < =========

# todo 需要缓存
def get_channel_subscribers_with_cache(cli, only_client=True):
    return Subscriber(redisc, cli=cli).get_channel_subscribers()


# todo 需要缓存
def get_subscriber_channels_with_cache(client_id):
    return Subscriber(redisc, client_id=client_id).get_subscriber_channels()