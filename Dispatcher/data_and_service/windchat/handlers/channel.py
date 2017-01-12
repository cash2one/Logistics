#coding=utf-8
__author__ = 'kk'

import traceback
from logging import error

from .models import Channel
from tools_lib.common_util.archived.pagination import paginator
from tools_lib.gtornado.web2 import ReqHandler
from tools_lib.windchat import http_utils

try:
    import ujson as json
except:
    import json


class BulkChannelHandler(ReqHandler):
    def get(self):
        """
        批量获得频道列表
        """
        try:
            data = self.get_query_args()
            page = int(data.get("page", 1))
            count = int(data.get("count", 10))

            # 仅包含被禁用的频道
            include_disabled = http_utils.bool_vs_query_string(data.get("include_disabled", "0"))

            # 仅包含置顶的频道
            only_top= http_utils.bool_vs_query_string(data.get("only_top", "0"))

            # 仅包含推荐首页的频道
            only_sticky = http_utils.bool_vs_query_string(data.get("only_sticky", "0"))

            # 是否要是以下管理员的频道
            manager_in = http_utils.dot_string_to_list(data.get("manager_in", ""))

            # 是否要是以下投稿人的频道
            poster_in = http_utils.dot_string_to_list(data.get("poster_in", ""))

            # 是否要是以下客服的频道
            answerer_in = http_utils.dot_string_to_list(data.get("answerer_in", ""))

            # 是否包含以下cli的频道
            cli_in = http_utils.dot_string_to_list(data.get("cli_in", ""))
        except:
            error(traceback.format_exc())
            self.resp_error("bad query string")
            return

        objs = Channel.objects().all()

        if not include_disabled:
            objs = objs.filter(disabled=False)

        if only_top:
            objs = objs.filter(top=True)

        if only_sticky:
            objs = objs.filter(sticky=True)

        if manager_in:
            objs = objs.filter(manager__in=manager_in)

        if poster_in:
            objs = objs.filter(poster__in=poster_in)

        if answerer_in:
            objs = objs.filter(answerer__in=answerer_in)

        if cli_in:
            objs = objs.filter(channel_leancloud_id__in=cli_in)

        p = paginator(None, objs, lambda x:x.id, page=page, count=count)
        self.set_x_resource_count(p[1])
        self.resp([i.format_response() for i in p[0]])


class ChannelHandler(ReqHandler):
    def post(self):
        """
        创建频道
        """
        channel_obj = Channel(**self.get_body_args())
        channel_obj.save()

        self.resp_created({
            "cli": channel_obj.channel_leancloud_id
        })

    def delete(self, cli):
        """
        禁用频道
        :param cli: 频道在leancloud的ID
        """
        r = Channel.objects(channel_leancloud_id=cli).first()
        if not r:
            self.resp_not_found("not found")
            return
        r.disabled = True
        r.save()
        self.resp_created()

    def patch(self, cli):
        """
        修改频道
        :param cli: 频道在leancloud的ID
        """
        data = self.get_body_args()
        r = Channel.objects(channel_leancloud_id=cli).first()
        for i in list(data.keys()):

            if i in (
                "cli", "channel_leancloud_id", # cli
                "create_time" # 创建时间
            ): continue
            setattr(r, i, data[i])
        r.save()

        self.resp_created()

    def get(self, cli):
        r = Channel.objects(channel_leancloud_id=cli).first()
        if not r:
            self.resp_not_found()
            return
        self.resp(r.format_response())
