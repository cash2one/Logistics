#coding=utf-8
__author__ = 'kk'

"""

models for LeanCloud to serve windchat conversations and message history.

"""

from leancloud import Object


class _Conversation(Object):
    """
    对话(频道或者聊天)
    """
    def __init__(self, **kwargs):
        super(_Conversation, self).__init__(**kwargs)
        # 以下各项参数请见文档 https://leancloud.cn/docs/realtime_v2.html
        self.set("attr", {})
        self.set("objectId", None)
        self.set("c", None)
        self.set("lm", None)
        self.set("m", [])
        self.set("mu", None)
        self.set("name", "")
        self.set("tr", False)
        self.set("sys", True)
        self.set("unique", False)


class _SysMessage(Object):
    """
    系统对话的聊天记录表
    """

    def __init__(self, **kwargs):
        super(_SysMessage, self).__init__(**kwargs)
        # 以下各项参数请见文档 https://leancloud.cn/docs/realtime_v2.html
        self.set("from", "")
        self.set("convId", "")
        self.set("msgId", "")
        self.set("fromIp", "")
        self.set("data", "")
