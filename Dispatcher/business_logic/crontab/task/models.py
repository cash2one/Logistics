#! /usr/bin/env python
# coding: utf-8
from mongoengine import Document, StringField, DictField, DateTimeField, FloatField, IntField
from datetime import datetime
from tools_lib.gmongoengine.utils import deduce_expect_fields, field_to_json


class Rewards(Document):
    """
    Model for Express.
    """
    m_type = StringField(default="", comment="奖励类型")
    title = StringField(default="", comment="事件标题")
    desc = StringField(default="", comment="事件描述")
    money = FloatField(default=0.0, comment="金额")
    create_time = DateTimeField(default=datetime.utcnow, comment=u'创建时间')
    man = DictField(default={}, comment="奖惩人员信息")
    source = DictField(default={}, comment="奖惩事件来源")

    meta = {
        'db_alias': 'aeolus_connection',
        'collection': 'rewards',
        'ordering': [
            '-create_time',
        ],
    }

    def pack(self, excludes=(), includes=(), only=()):
        # 有可能传None进来,set(None)会报错
        expected = deduce_expect_fields([f for f in self], excludes, includes, only)

        packed = {}
        for field in expected:
            value = self[field] if hasattr(self, field) else None
            packed[field] = field_to_json(value)
        return packed


class Settlement(Document):
    base = FloatField(default=0.0, comment="基础服务费")
    insurance = FloatField(default=0.0, comment="保险")
    reward = FloatField(default=0.0, coment="奖励")
    punishment = FloatField(default=0.0, coment="惩罚")
    sj_profit = FloatField(default=0)
    pj_profit = FloatField(default=0)
    total = FloatField(default=0)
    create_time = DateTimeField(default=datetime.utcnow, comment=u'创建时间')
    man = DictField(default={}, comment="人员信息")
    meta = {
        'db_alias': 'aeolus_connection',
        'collection': 'settlement',
        'ordering': [
            '-create_time',
        ],
    }

    def pack(self, excludes=(), includes=(), only=()):
        # 有可能传None进来,set(None)会报错
        expected = deduce_expect_fields([f for f in self], excludes, includes, only)
        packed = {}
        for field in expected:
            value = getattr(self, field) if hasattr(self, field) else None
            packed[field] = field_to_json(value)

        return packed


class OpData(Document):
    zj_top_up = IntField(default=0, comment="充值")
    zj_pay = IntField(default=0, comment="消费")
    zj_cash_back = IntField(default=0, comment="返现")
    zj_cost = IntField(default=0, comment='成本')
    zj_profit_rate = IntField(default=0, comment='利润率')

    dd_count = IntField(default=0, comment="下单量")
    dd_sj_count = IntField(default=0, comment="接单量")
    dd_tt_count = IntField(default=0, comment="妥投量")
    dd_error_count = IntField(default=0, comment="异常量")
    dd_average_price = FloatField(default=0, comment='客单价')

    sh_visit = IntField(default=0, comment="客户拜访量")
    sh_register = IntField(default=0, comment="客户注册量")
    sh_order = IntField(default=0, comment="当日客户下单量")
    sh_valid = IntField(default=0, comment="当日系统审核通过的客户总数")
    sh_complain = IntField(default=0, comment="客户投诉")
    sh_first_order = IntField(default=0, comment='当日首次下单的客户数')
    sh_total = IntField(default=0, comment="当日客户库内总客户数")

    hr_registered = IntField(default=0, comment="当日注册配送员")
    hr_on_job = IntField(default=0, comment="当日在职配送员")
    hr_active = IntField(default=0, comment="当日活跃配送员")
    hr_break = IntField(default=0, comment="当日请假配送员")
    hr_leave = IntField(default=0, comment="当日离职配送员")
    hr_junior_captain_on_job = IntField(default=0, comment="当日在职小队长")
    hr_squadron_leader_on_job = IntField(default=0, comment="当日在职中队长")
    hr_driver_on_job = IntField(default=0, comment="当日在职司机")

    hr_entry = IntField(default=0, comment="当日入职配送员数，非working转working")
    hr_interview = IntField(default=0, comment="当日面试配送员数，非wokring状态的在星耀城风先生大楼签到的人数")
    hr_invite = IntField(default=0, comment="当日电话邀约数，新安装配送员APP的人数")
    hr_consulting = IntField(default=0, comment="当日投简历, 呼入数")

    cl_depart = IntField(default=0, comment="当日出勤司机（非蓝城项目）")
    cl_shift = IntField(default=0, comment="当日司机在指定站点签到数")
    cl_late = IntField(default=0, comment="当日司机签到迟到数")
    cl_mileage = IntField(default=0, comment='当日所有车辆总里程')

    rj_fh_update = IntField(default=0, comment="当日发货端更新数")
    rj_ps_update = IntField(default=0, comment="当日收派端更新数")

    create_time = DateTimeField(default=datetime.utcnow, comment=u'创建时间')
    meta = {
        'db_alias': 'aeolus_connection',
        'collection': 'op_data',
        'ordering': [
            '-create_time',
        ]
    }

    def pack(self, excludes=(), includes=(), only=()):
        # 有可能传None进来,set(None)会报错
        expected = deduce_expect_fields([f for f in self], excludes, includes, only)
        packed = {}
        for field in expected:
            value = getattr(self, field) if hasattr(self, field) else None
            packed[field] = field_to_json(value)

        return packed
