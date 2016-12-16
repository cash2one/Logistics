# coding: utf-8
from __future__ import unicode_literals
import arrow
from datetime import datetime

from bson import ObjectId
from mongoengine import Document, EmbeddedDocument, DictField, StringField, IntField, DateTimeField
from tools_lib.common_util.sstring import safe_unicode


# ===> 服务评价 <===
class Evaluate(Document):
    call_id = StringField(default=None, help_text="呼叫id")
    number = StringField(help_text="运单号")
    origin = DictField(help_text="来源人员信息")
    # origin_type node_0发货端 node_n收货者
    # id 人员id(如果有)
    # name 姓名
    # tel 电话
    rate = IntField(help_text="评分")
    comment = StringField(help_text="备注")
    create_time = DateTimeField(default=arrow.utcnow)

    meta = {
        'db_alias': 'coolie_connection',
        'collection': 'evaluate',
        'ordering': [
            '-create_time',
        ],
        'indexes': [
            'call_id',
            'origin.tel',
            'origin.id',
            'origin.origin_type',
            'rate',
            'create_time',
        ]
    }

    @classmethod
    def _field_to_json(cls, field):
        ret = field
        if isinstance(field, ObjectId):
            ret = safe_unicode(str(field))
        elif isinstance(field, datetime):
            ret = TimeZone.utc_to_local(field)
        elif isinstance(field, EmbeddedDocument):
            if hasattr(field, "pack"):
                ret = field.pack()
        elif isinstance(field, Document):
            if hasattr(field, "pack"):
                ret = field.pack()
            else:
                ret = safe_unicode(field.pk)
        elif isinstance(field, list):
            ret = [cls._field_to_json(_) for _ in field]
        elif isinstance(field, dict):
            ret = {k: cls._field_to_json(v) for k, v in field.iteritems()}
        elif isinstance(field, float):
            ret = round(ret, 2)
        return ret

    def pack(self, only=()):
        packed = {}
        for field in only:
            value = self[field] if hasattr(self, field) else None
            packed[field] = self._field_to_json(value)
        return packed
