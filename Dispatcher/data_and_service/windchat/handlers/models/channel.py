#coding=utf-8
__author__ = 'kk'

from leancloud.query import Query

from mongoengine import (Document, StringField, BooleanField, ListField, DictField, DateTimeField)
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.common_util.third_party.image import get_image_url
from tools_lib.leancloud.models import _Conversation


class Channel(Document):
    """
    频道

    * subscriber_condition: 订阅者条件
    "man": "all" 全部配送员都订阅


    """
    channel_leancloud_id = StringField(help_text="频道在leancloud上的ID, 'cli' for short")
    name = StringField(default="new channel", help_text="频道名")
    description = StringField(default="", help_text="描述")
    icon = StringField(default="", help_text="图标hash")
    sticky = BooleanField(default=False, help_text="频道内文章放入最新文章列表")
    top = BooleanField(default=False, help_text="频道在列表置顶")
    talkable = BooleanField(default=True, help_text="频道可聊天")
    disabled = BooleanField(default=False, help_text="禁用")
    manager = ListField(default=list, help_text="管理员")
    answerer = ListField(default=list, help_text="应答员")
    subscriber_condition = DictField(default=dict, help_text="收听者绑定条件,如果存在这样的条件,则会有定时任务去更新subscriber(redis)")
    answerer_condition = DictField(default=dict, help_text="客服绑定条件")
    create_time = DateTimeField(default=TimeZone.utc_now)
    update_time = DateTimeField()

    meta = {
        "collection": "channel",
        "indexes": [
            "channel_leancloud_id",
            "name",
            "sticky",
            "top",
            "talkable",
            "disabled"
        ]
    }

    def format_response(self):
        return {
            "cli": self.channel_leancloud_id,
            "name": self.name,
            "description": self.description,
            "icon": get_image_url(self.icon),
            "sticky": self.sticky,
            "top": self.top,
            "talkable": self.talkable,
            "disabled": self.disabled,
            "manager": self.manager,
            "answerer": self.answerer,
            "subscriber_condition": self.subscriber_condition,
            "create_time": TimeZone.datetime_to_str(self.create_time)
        }

    def save(self, *args, **kwargs):
        """
        重写保存
        """
        # 保存的时候检查有没有leancloud的conversation,没有则创建
        if not self.channel_leancloud_id:
            cl_c = _Conversation()
            cl_c.set("n", self.name)
            cl_c.set("sys", True)
            cl_c.save()
            self.channel_leancloud_id = cl_c.id
        else:
            qs = Query(_Conversation)
            cl_c = qs.get(self.channel_leancloud_id)
            if cl_c.get("name")!=self.name:
                cl_c.set("name", self.name)
                cl_c.save()
            # 更新 update_time
            self.update_time = TimeZone.utc_now()
        super(Channel, self).save(*args, **kwargs)