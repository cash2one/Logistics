#!/usr/bin/env python
# coding:utf-8

"""
Models for shop
"""

from tools_lib.transwarp.orm import Model, StringField, FloatField, DateTimeField, IntegerField
from tools_lib.transwarp.tz import utc_now
from tools_lib.transwarp.web import Dict
from mongoengine import (Document, StringField as MStringField, DictField, DateTimeField as MDateTimeField,
                         DynamicField)

TRANSACT_TYPE = Dict(**{k: k for k in ('TOP_UP', 'PAY', 'REFUND', 'CASH_OUT', 'CASH_BACK')})


class Statistics(Model):
    __table__ = 'flow_statistics'
    shop_id = StringField(nullable=False, ddl='char(24)', primary_key=True, comment='商户ID')
    shop_name = StringField(default='', nullable=True, ddl='varchar(64)', comment='商户名称')
    balance = FloatField(default=.0, nullable=False, ddl='decimal(10,2)', comment='充值余额(元)')
    expense = FloatField(default=.0, nullable=False, ddl='decimal(10,2)', comment='消费金额(元)')


class Flow(Model):
    __table__ = 'flow'
    transact_num = StringField(ddl='char(14)', primary_key=True, comment='商户充值时对应flow_top_up.order_no')
    shop_id = StringField(default=None, nullable=False, ddl='char(24)', comment='商户id', key=True)
    shop_name = StringField(default='', nullable=True, ddl='varchar(64)', comment='商户名称')
    shop_tel = StringField(default=None, nullable=False, ddl='char(11)', comment='商户登录手机号', key=True)

    type = StringField(default=None, nullable=False, ddl='char(14)',
                       comment='交易类型: TOP_UP:充值 PAY:消费 REFUND:退款 CASH_OUT:线下退款', key=True)
    cash = FloatField(nullable=False, ddl='decimal(10,2)', comment='交易金额(元)')
    balance = FloatField(nullable=False, ddl='decimal(10,2)', comment='该笔交易后余额')

    remark = StringField(default='', nullable=True, ddl='varchar(64)', comment='交易备注')

    create_time = DateTimeField(key=True, comment='充值对应的是:充值成功回调返回的pay_time')


class TopUp(Model):
    __table__ = 'flow_top_up'
    transact_num = IntegerField(ddl='char(14)', primary_key=True)
    shop_id = StringField(default=None, nullable=False, ddl='char(24)', comment='商户id', key=True)
    shop_name = StringField(default='', nullable=True, ddl='varchar(64)', comment='商户名称')
    shop_tel = StringField(default=None, nullable=False, ddl='char(11)', comment='商户登录手机号', key=True)

    cash = FloatField(nullable=False, ddl='decimal(10,2)', comment='尝试充值金额(元)')
    create_time = DateTimeField(key=True)

    trade_no = StringField(nullable=True, ddl='varchar(32)', comment='第三方支付回调返回的交易号')
    result = StringField(nullable=True, ddl='varchar(32)', comment='第三方支付通知的结果')


class ShopFSMLog(Model):
    """风先生商户状态变更日志Model, 存储状态变更日志"""
    __table__ = 'shop_fsm_log'

    id = IntegerField(ddl='int(11) unsigned', primary_key=True)
    shop_id = StringField(default=None, nullable=False, ddl='char(24)', comment='商户ID', key=True)
    shop_name = StringField(default='', nullable=True, ddl='varchar(18)', comment='商户姓名', key=True)
    from_status = StringField(default='', nullable=False, ddl='varchar(32)', comment='从哪个状态')
    to_status = StringField(default='', nullable=False, ddl='varchar(32)', comment='变为哪个状态')
    event = StringField(default='', nullable=False, ddl='varchar(32)', comment='触发事件')
    operator_type = StringField(default='', nullable=False, ddl='char(10)', comment='事件来源: FE_OUTSIDE或FE_INSIDE')
    operator_id = StringField(ddl='varchar(24)', comment='后台操作人ID')
    remark = StringField(default='', nullable=True, ddl='varchar(128)', comment='操作备注;FE_OUTSIDE端显示的通知内容;')

    create_time = DateTimeField(key=True, auto_now_add=True)


class Shop(Document):
    tel = MStringField(max_length=11, unique=True, comment="11位手机号, 要求唯一")
    password = MStringField(min_length=32, max_length=32, comment="密码")

    name = MStringField(default=None, max_length=64, comment="商户名")
    status = MStringField(max_length=32, default='STATUS_VALID', comment="商户状态")
    contact = DynamicField(comment='联系人: name, tel')

    loc = DictField(default=dict, comment="商户所属地址: address, lat,lng")
    # 预计单量,货物类型,平均体积,时效要求, 需求描述
    requirement = DynamicField(comment='商户配送需求: forecast_orders,cargo_type,average_size,time_limit,remark')
    recommended_by = DynamicField(default=None, comment='推荐人: tel,time')

    fee = DictField(default=None, comment='商户定价: fh, ps, ...')

    create_time = MDateTimeField(default=utc_now, comment="创建时间")

    meta = {
        "db_alias": "profile_connection",
        'collection': 'shop',
        'ordering': [
            '-create_time',
        ],
        'indexes': [
            'tel',
            'name',
            'create_time'
        ]
    }


if __name__ == "__main__":
    print((Flow().__sql__()))
