#!/usr/bin/env python
# coding:utf-8

"""
Models for payroll
"""

from tools_lib.transwarp.orm import Model, IntegerField, StringField, DateTimeField


class TrackingNumber(Model):
    """生成面单号Model, 存储已经生成的号码信息"""
    __table__ = 'tracking_number'

    tracking_number = IntegerField(ddl='int(11)', comment="面单号", primary_key=True)
    # tracking_number = StringField(default=None, nullable=False, ddl='char(12)', comment=u'面单号', key=True)

    create_time = DateTimeField(auto_now_add=True, comment="本地时间 UTC+8:00", key=True)  # UTC+8:00

    def __hash__(self):
        return hash("%d" % self.id)

    def __eq__(self, other):
        return self.id == other.id


if __name__ == "__main__":
    print((TrackingNumber().__sql__()))
