#coding=utf-8
__author__ = 'kk'

"""

lean-cloud IM SDK by kk

"""

__all__ = ["Rtm", "AsyncRtm"]

import time
import hashlib
import logging
import requests
from tools_lib.gtornado import async_requests

try:
    import ujson as json
except:
    import json


class BasicRtm(object):
    def __init__(self, app_id, app_key, master_key):
        self.app_id = app_id
        self.app_key = app_key
        self.master_key = master_key
        self.default_headers = { # 用于验证app key的头
            "X-LC-Id": self.app_id,
            "X-LC-Key": self.app_key
        }
        self.master_key_headers = { # 用于验证master key的头
            "X-LC-Id": self.app_id,
            "X-LC-Key": "%s,master" % self.master_key
        }


class AsyncRtm(BasicRtm):
    """
    tornado 版的 sdk
    """
    def conversation_history(self,
        convid,
        max_ts=None,
        msgid=None,
        limit=None,
    ):
        """
        获取消息历史
        """
        url = "https://leancloud.cn/1.1/rtm/messages/logs"
        qs = {"convid":convid}
        if max_ts: qs.update({"max_ts": max_ts})
        if msgid: qs.update({"msgid": msgid})
        if limit: qs.update({"limit": limit})
        return async_requests.get(url, headers=self.master_key_headers, params=qs)

    def conversation_history_sys(self, sys_cvs_id, client_id, *args, **kwargs):
        """
        获取系统对话中某个client的消息历史
        > 这个是基于conversation_history包装的
        :param sys_cvs_id: 系统对话ID
        :param client_id: 用户ID
        """
        convid = hashlib.md5("%s:%s" % (sys_cvs_id, client_id)).hexdigest()
        return self.conversation_history(convid=convid, *args, **kwargs)

    def conversation_remove_history(self, convid, msgid, timestamp=None):
        """
        删除消息历史
        """
        url_tmpl = "https://leancloud.cn/1.1/rtm/messages/logs"
        if not timestamp: timestamp = int(time.time())
        return async_requests.delete(url_tmpl, headers=self.master_key_headers, params={
            "convid": convid,
            "msgid": msgid,
            "timestamp": timestamp
        })

    def send_message(
            self,
            from_peer,
            conv_id,
            message,
            to_peers=None,
            transient=False,
            no_sync=False,
    ):
        """
        发送消息
        """
        url = "https://leancloud.cn/1.1/rtm/messages"
        return async_requests.post(
            url=url,
            headers=self.master_key_headers,
            json={
                "from_peer": from_peer,
                "conv_id": conv_id,
                "message": message,
                "to_peers": to_peers,
                "transient": transient,
                "no_sync": no_sync
            }
        )


class Rtm(BasicRtm):
    """
    requests 版的 sdk
    """
    def send_message(
            self,
            from_peer,
            conv_id,
            message,
            to_peers=None,
            transient=False,
            no_sync=False,
    ):
        """
        使用tornado非阻塞发送消息
        """
        url = "https://leancloud.cn/1.1/rtm/messages"
        return requests.post(
            url=url,
            headers=self.master_key_headers,
            json={
                "from_peer": from_peer,
                "conv_id": conv_id,
                "message": message,
                "to_peers": to_peers,
                "transient": transient,
                "no_sync": no_sync
            },
            verify=False # 因为209上面系统问题
        )
