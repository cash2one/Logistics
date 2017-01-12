# coding:utf-8

from tools_lib.transwarp.orm import Model, StringField, IntegerField, FloatField, DateTimeField
from tools_lib.transwarp.web import Dict
from tools_lib.transwarp.tz import utc_now
from mongoengine import (Document, StringField as MStringField, ListField, DictField, DateTimeField as MDateTimeField,
                         DynamicField)

# 全局变量
CASH_FLOW = Dict(**{x: x for x in ('VALIDATED', 'APPLY_WITHDRAW', 'PAID', 'DECLINE')})


class ManFSMLog(Model):
    """风先生派件员状态变更日志Model, 存储状态变更日志"""
    __table__ = 'man_fsm_log'

    id = IntegerField(ddl='int(11) unsigned', primary_key=True)
    man_id = StringField(default=None, nullable=False, ddl='char(24)', comment='派件员ID', key=True)
    man_name = StringField(default='', nullable=True, ddl='varchar(18)', comment='派件员姓名', key=True)
    from_status = StringField(default='', nullable=False, ddl='varchar(32)', comment='从哪个状态')
    to_status = StringField(default='', nullable=False, ddl='varchar(32)', comment='变为哪个状态')
    event = StringField(default='', nullable=False, ddl='varchar(32)', comment='触发事件')
    operator_type = StringField(default='', nullable=False, ddl='char(3)', comment='事件来源: FE或APP')
    operator_id = StringField(ddl='varchar(24)', comment='后台操作人ID')
    remark = StringField(default='', nullable=True, ddl='varchar(128)', comment='操作备注;APP端显示的通知内容;')

    create_time = DateTimeField(key=True, auto_now_add=True)


class Statistics(Model):
    __table__ = 'flow_statistics'
    man_id = StringField(nullable=False, ddl='char(24)', primary_key=True)
    man_name = StringField(nullable=True, ddl='varchar(16)', key=True)
    can_cash = FloatField(default=.0, nullable=False, ddl='decimal(10,2)', comment='可提现金额(元)')
    finance = FloatField(default=.0, nullable=False, ddl='decimal(10,2)', comment='待财务处理(元)')
    paid = FloatField(default=.0, nullable=False, ddl='decimal(10,2)', comment='财务已付款(元)')
    decline = FloatField(default=.0, nullable=False, ddl='decimal(10,2)', comment='财务已拒绝(元)')


class Flow(Model):
    __table__ = 'flow'
    transact_num = StringField(ddl='char(14)', primary_key=True)
    man_id = StringField(default=None, nullable=False, ddl='char(24)', comment='众包派件员uuid', key=True)
    tel = StringField(default=None, nullable=False, ddl='char(11)', comment='众包派件员手机号', key=True)

    type = StringField(default=None, nullable=False, ddl='char(14)',
                       comment='流水类型: VALIDATED:已审核订单金额 APPLY_WITHDRAW:申请提现金额 PAID:财务已付款金额 DECLINE:财务已拒绝金额', key=True)
    cash = FloatField(nullable=False, ddl='decimal(10,2)', comment='金额(元)')

    # VALIDATED没有, 其他有.
    account_id = StringField(nullable=True, ddl='varchar(64)', comment='(提现)支付宝的账户id', key=True)
    account_name = StringField(nullable=True, ddl='varchar(32)', comment='(提现)支付宝账户id对应的姓名')

    expr_num = StringField(nullable=True, ddl='char(12)', comment='运单号')
    operator_id = StringField(nullable=True, ddl='varchar(24)', comment='后台操作人ID')
    remark = StringField(default='', nullable=True, ddl='varchar(64)', comment='后台操作备注')

    create_time = DateTimeField(key=True)
    update_time = DateTimeField(key=True)


class Man(Document):
    job_description = DynamicField(comment='角色: []')
    tel = MStringField(max_length=11, unique=True, comment='11位手机号, 要求唯一')
    id_card_num = MStringField(min_length=18, max_length=18, comment='身份证号')

    name = MStringField(max_length=18, comment='姓名')
    avatar = MStringField(max_length=36, comment='头像/身份证正面照hash')
    id_card_back = MStringField(max_length=36, comment='身份证反面照hash')

    status = MStringField(max_length=32, default='STATUS_INIT', comment='人员状态')
    create_time = MDateTimeField(default=utc_now, comment='创建时间')

    accounts = ListField(DictField(), default=list, comment='支付宝账户: id, name')
    familiars = ListField(DictField(), default=list, comment='熟悉地点: name, city, addr, lng, lat')

    recommended_by = DictField(default=dict, comment='推荐人: tel, time')

    # ==> 以下字段只属于[派件员]
    my_manager = DictField(default=None, comment='我的区域经理: id, name, tel, bind_time')
    # ==> 以下字段只属于[区域经理]
    my_man = ListField(DictField(), default=None, comment='我的派件员们: id, name, tel, bind_time')
    pick_up_locations = ListField(DictField(), default=None, comment='我的取货点: name, city, addr, lng, lat')

    meta = {
        'db_alias': 'profile_connection',
        'collection': 'man',
        'ordering': [
            '-create_time',
        ],
        'indexes': [
            'tel',
            'name',
            'create_time'
        ]
    }


class SignIn(Document):
    man_id = MStringField(min_length=24, max_length=24, comment='24位人员id')
    name = MStringField(max_length=18, comment='姓名')
    tel = MStringField(max_length=11, comment='11位手机号')
    avatar = MStringField(max_length=36, comment='头像/身份证正面照hash')

    loc = DictField(comment='我的签到地点: name, addr, lng, lat')
    device = DictField(comment='我的签到手机机型相关: mac_id, ...')

    create_time = MDateTimeField(default=utc_now, unique=True, comment='签到时间')

    meta = {
        'db_alias': 'profile_connection',
        'collection': 'sign_in',
        'ordering': [
            '-create_time',
        ],
        'indexes': [
            'man_id',
            'tel',
            'name',
            'create_time'
        ]
    }


class Staff(Document):
    """内部员工Model, 存储员工基础信息"""
    job_description = MStringField(comment='岗位类型')
    tel = MStringField(max_length=11, unique=True, comment='11位手机号, 要求唯一')
    id_card_num = MStringField(min_length=18, max_length=18, comment='身份证号')
    password = MStringField(min_length=32, max_length=32, comment='密码')

    name = MStringField(max_length=18, comment='姓名')
    avatar = MStringField(max_length=36, comment='头像')

    status = MStringField(max_length=32, default='STATUS_WORKING', comment='员工在职状态')
    create_time = MDateTimeField(default=utc_now, comment='创建时间')

    meta = {
        'db_alias': 'profile_connection',
        'collection': 'staff',
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
    print((ManFSMLog().__sql__()))
    print((Statistics().__sql__()))
    print((Flow().__sql__()))
