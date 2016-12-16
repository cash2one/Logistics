# coding=utf-8
__author__ = 'kk'

from datetime import datetime

from mongoengine import (Document, StringField, DictField, DateTimeField, PolygonField)
from tools_lib.gmongoengine.utils import field_to_json_no_round


class Fence(Document):
    """
    栅栏
    """
    name = StringField(default="", max_length=32, help_text="栅栏名")
    loc = DictField(default=dict, help_text="车辆停靠点")
    points = PolygonField(help_text="栅栏节点")
    color = StringField(default="", max_length=64, help_text="显示颜色")
    manager = DictField(default=dict, help_text="栅栏负责人")
    create_time = DateTimeField(default=datetime.utcnow)

    meta = {
        'db_alias': 'aeolus_connection',
        'collection': 'fence',
        'ordering': ['name']
    }

    def __init__(self, *args, **values):
        if '_id' in values:
            values['id'] = values['_id']
            del values['_id']

        super(Fence, self).__init__(*args, **values)

    def __str__(self):
        return "<Fence object id(%s)>" % (self.id)

    def verify(self):
        """
        判断栅栏是否合乎逻辑
        """
        return True

    def format_response(self, skip_field=None):
        json_data = {}
        for field in self:
            if skip_field is not None and field in skip_field:
                continue
            value = self[field]
            if field == 'points' and isinstance(value, dict):
                value = value['coordinates']
            json_data[field] = field_to_json_no_round(value)
        return json_data
