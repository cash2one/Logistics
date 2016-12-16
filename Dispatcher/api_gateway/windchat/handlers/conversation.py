#coding=utf-8
__author__ = 'kk'

from leancloud.query import Query, LeanCloudError
from schema import Schema
from tornado import gen

from tools_lib.gtornado.escape import schema_utf8
from tools_lib.gtornado.web2 import ReqHandler
from tools_lib.leancloud.models import _Conversation
from tools_lib.windchat import http_utils


class UnreadHandler(ReqHandler):
    @gen.coroutine
    def get(self):
        pass

    @gen.coroutine
    def post(self):
        pass

    @gen.coroutine
    def delete(self):
        pass


class ConversationHandler(ReqHandler):
    def logic(self, client_ids):
        if len(client_ids)<=1:
            self.resp_error(content="At least two client_id is required.")
            return
        try_same = None
        for i in client_ids:
            if not i or try_same==i:
                self.resp_args_error()
                return
            try_same = i
        qs = Query(_Conversation)
        try:
            obj = qs.contains_all("m", client_ids).first() # FIXME 当前只是包含, 如果今后出现了群聊,此处务必修改
            the_id = obj.id
        except LeanCloudError:
            conv_obj = _Conversation()
            conv_obj.set("m", client_ids)
            conv_obj.set("sys", False)
            conv_obj.save()
            the_id = conv_obj.id
        return the_id

    @gen.coroutine
    def get(self):
        """
        获取对话 id
        :return:
        """
        data = self.get_query_args()
        client_ids = http_utils.dot_string_to_list(data["client_ids"])
        self.resp({
            "conversation_id": self.logic(client_ids)
        })

    @gen.coroutine
    def post(self):
        """
        批量获取对话
        :return:
        """
        data = Schema([
            [schema_utf8, schema_utf8]
        ]).validate(self.get_body_args())
        self.resp([self.logic(i) for i in data])
