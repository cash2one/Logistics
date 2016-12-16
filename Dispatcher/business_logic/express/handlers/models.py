# coding:utf-8
from __future__ import unicode_literals

import arrow
from datetime import datetime

from bson import ObjectId
from mongoengine import (EmbeddedDocument, Document, StringField, DictField, DateTimeField, ListField,
                         IntField, PointField, Q, PolygonField)
from tools_lib.common_util.sstring import safe_unicode
from tools_lib.gtornado.apis import generate_number
from tools_lib.transwarp.tz import utc_now, utc_to_local
from tornado import gen


class ApiError(Exception):
    pass


class DuplicateDocError(Exception):
    pass


class Node(Document):
    """
    站点: 带时刻人员表
    """
    name = StringField(min_length=1, max_length=64, unique=True, comment='站点名称')  # 不允许重名, unique以后会自己index
    color = StringField(default="", max_length=64, comment="围栏显示颜色")

    loc = DictField(default=dict, comment='lat,lng,address...')
    point = PointField(comment='用于mongodb地理操作支持')
    time_table = ListField(default=list, comment='[{t=t, man={id, name, tel, m_type, client_id}},...]')

    create_time = DateTimeField(default=utc_now, comment='创建时间')
    update_time = DateTimeField(default=utc_now, comment='更新时间')

    meta = {
        'db_alias': 'aeolus_connection',
        'collection': 'node',
        'ordering': [
            '-update_time',
        ],
        'indexes': [
            '(point',  # "2dsphere"
            'time_table.t',
            'time_table.man.id',
            'time_table.man.tel',
        ]
    }

    def update(self, **kwargs):
        kwargs.update({'set__update_time': utc_now()})
        return super(Node, self).update(**kwargs)

    def modify(self, **kwargs):
        kwargs.update({'set__update_time': utc_now()})
        return super(Node, self).update(**kwargs)

    def save(self, **kwargs):
        self.update_time = utc_now()
        return super(Node, self).save(**kwargs)

    @staticmethod
    def _field_to_json(value):
        ret = value
        if isinstance(value, ObjectId):
            ret = safe_unicode(str(value))
        elif isinstance(value, datetime):
            ret = utc_to_local(value)
        elif isinstance(value, EmbeddedDocument):
            if hasattr(value, "pack"):
                ret = value.pack()
        elif isinstance(value, Document):
            if hasattr(value, "pack"):
                ret = value.pack()
            else:
                ret = safe_unicode(value.pk)
        elif isinstance(value, list):
            ret = [Node._field_to_json(_) for _ in value]
        elif isinstance(value, dict):
            ret = {k: Node._field_to_json(value[k]) for k in value}
        return ret

    def pack(self, only=()):
        only = only if only else ()

        expected = only
        if not only:
            # 有only只返回only; 没有only, 计算需要的字段: (_db_field_map | includes) - excludes
            expected = set([f for f in self])

        packed = {}
        for field in expected:
            value = self[field] if hasattr(self, field) else None
            packed[field] = Node._field_to_json(value)
        return packed


class Schedule(Document):
    """
    人员: 带时刻站点表
    """
    man = DictField(default=dict, comment='id, name, tel, m_type, client_id')

    run = ListField(default=list, comment='[{t=t, name=name, loc={lat,lng,address}},...]')

    create_time = DateTimeField(default=utc_now, comment='创建时间')
    update_time = DateTimeField(default=utc_now, comment='更新时间')

    meta = {
        'db_alias': 'aeolus_connection',
        'collection': 'schedule',
        'ordering': [
            '-update_time',
        ],
        'indexes': [
            'man.id',
            'man.tel',
            'man.name',
            'run.name',
        ]
    }

    def update(self, **kwargs):
        kwargs.update({'set__update_time': utc_now()})
        return super(Schedule, self).update(**kwargs)

    def modify(self, **kwargs):
        kwargs.update({'set__update_time': utc_now()})
        return super(Schedule, self).update(**kwargs)

    def save(self, **kwargs):
        self.update_time = utc_now()
        return super(Schedule, self).save(**kwargs)

    @staticmethod
    def _field_to_json(value):
        ret = value
        if isinstance(value, ObjectId):
            ret = safe_unicode(str(value))
        elif isinstance(value, datetime):
            ret = utc_to_local(value)
        elif isinstance(value, EmbeddedDocument):
            if hasattr(value, "pack"):
                ret = value.pack()
        elif isinstance(value, Document):
            if hasattr(value, "pack"):
                ret = value.pack()
            else:
                ret = safe_unicode(value.pk)
        elif isinstance(value, list):
            ret = [Schedule._field_to_json(_) for _ in value]
        elif isinstance(value, dict):
            ret = {k: Schedule._field_to_json(value[k]) for k in value}
        return ret

    def pack(self, only=()):
        only = only if only else ()

        expected = only
        if not only:
            # 有only只返回only; 没有only, 计算需要的字段: (_db_field_map | includes) - excludes
            expected = set([f for f in self]) - {'id'}

        packed = {}
        for field in expected:
            value = self[field] if hasattr(self, field) else None
            packed[field] = Schedule._field_to_json(value)
        return packed


class Fence(Document):
    """
    围栏: 带站点和人员信息
    """
    name = StringField(default="", max_length=64, unique=True, comment="围栏名")  # 不允许重名
    points = PolygonField(comment="围栏节点")

    node = DictField(default=dict, comment='站点:id, name, loc={lat,lng,address}')  # 围栏表示站点辐射范围, 与站点是多对一的关系
    mans = ListField(DictField(), default=list, comment='围栏下的人员: [{id, name, tel, m_type, client_id},...]')

    create_time = DateTimeField(default=utc_now, comment='创建时间')
    update_time = DateTimeField(default=utc_now, comment='更新时间')

    meta = {
        'db_alias': 'aeolus_connection',
        'collection': 'fence',
        'ordering': [
            '-update_time',
        ],
        'indexes': [
            'name',
            'node.name',
            # 'node.address',
            'mans.id',
            'mans.name',
            'mans.tel',
            # 'mans.m_type',
        ]
    }

    @staticmethod
    def _field_to_json(value):
        ret = value
        if isinstance(value, ObjectId):
            ret = safe_unicode(str(value))
        elif isinstance(value, datetime):
            ret = utc_to_local(value)
        elif isinstance(value, EmbeddedDocument):
            if hasattr(value, "pack"):
                ret = value.pack()
        elif isinstance(value, Document):
            if hasattr(value, "pack"):
                ret = value.pack()
            else:
                ret = safe_unicode(value.pk)
        elif isinstance(value, list):
            ret = [Fence._field_to_json(_) for _ in value]
        elif isinstance(value, dict):
            ret = {k: Fence._field_to_json(value[k]) for k in value}
        return ret

    def pack(self, only=()):
        only = only if only else ()

        expected = only
        if not only:
            # 有only只返回only; 没有only, 计算需要的字段: (_db_field_map | includes) - excludes
            expected = set([f for f in self])

        packed = {}
        for field in expected:
            value = self[field] if hasattr(self, field) else None
            packed[field] = Fence._field_to_json(value)
        return packed


class Call(Document):
    # 呼叫任务入口: 只有在所有number_list中的运单(如有)主状态在SENDING,FINISHED的时候才提供入口.
    status = StringField(default='ALL', comment='ALL/ASSIGNED/BE_IN_PROCESS/CLOSABLE/CLOSED')
    shop_id = StringField(min_length=24, max_length=32, comment='寄方id')
    shop_name = StringField(max_length=64, comment='寄方名称')
    shop_tel = StringField(min_length=1, max_length=14, comment='寄方手机号')

    loc = DictField(default=dict, comment='lat,lng,address,fence{id, name}')

    count = IntField(min_value=1, max_value=200, comment='商户说我要发多少单')
    number_list = ListField(default=list, comment='商户发起的呼叫有没有被满足(粗略判断): 代商户填单 运单编号列表')

    watchers = ListField(default=None,
                         comment='所有能看到这次呼叫的人: [{id,name,tel,m_type,client_id: 其中m_type为角色,暂时记录app-name}]')
    assignee = DictField(default=dict, comment='id,name,tel,m_type')
    transact_list = ListField(default=list, comment='[{transact_num,cash,number_list,code_url, trade_no},...]')

    msg = StringField(default=None, max_length=256, comment='没找到站点,记录下具体信息')

    create_time = DateTimeField(default=utc_now, comment='创建时间')
    update_time = DateTimeField(default=utc_now, comment='更新时间: 最新代商户填单时间')

    meta = {
        'db_alias': 'aeolus_connection',
        'collection': 'call',
        'ordering': [
            '-create_time',
        ],
        'indexes': [
            'shop_id',
            'shop_tel',
            'number_list',
            'create_time'
        ]
    }

    def update(self, **kwargs):
        kwargs.update({'set__update_time': utc_now()})
        return super(Call, self).update(**kwargs)

    def modify(self, **kwargs):
        kwargs.update({'set__update_time': utc_now()})
        return super(Call, self).modify(**kwargs)

    def save(self, **kwargs):
        self.update_time = utc_now()
        return super(Call, self).save(**kwargs)

    @classmethod
    def filter_call(cls, kw, excludes=(), only=()):
        includes = {'add_to_set__number_list', 'push__transact_list'}
        excludes = excludes if excludes else ()
        only = only if only else ()
        expected = only
        if not expected:
            # 有only只返回only; 没有only, 计算需要的字段: _db_field_map | includes - excludes
            expected = (set(cls._db_field_map) | set(includes)) - set(excludes)
        filtered = {}
        for k in expected:
            if k in kw:
                filtered[k] = kw[k]
        return filtered

    @staticmethod
    def _field_to_json(value):
        ret = value
        if isinstance(value, ObjectId):
            ret = safe_unicode(str(value))
        elif isinstance(value, datetime):  # 从mongodb返回的utc时间
            ret = arrow.get(value).to('local').isoformat()
        elif isinstance(value, EmbeddedDocument):
            if hasattr(value, "pack"):
                ret = value.pack()
        elif isinstance(value, Document):
            if hasattr(value, "pack"):
                ret = value.pack()
            else:
                ret = safe_unicode(value.pk)
        elif isinstance(value, list):
            ret = [Call._field_to_json(_) for _ in value]
        elif isinstance(value, dict):
            ret = {k: Call._field_to_json(value[k]) for k in value}
        return ret

    def pack(self, only=()):
        only = only if only else ()

        expected = only
        if not only:
            # 有only只返回only; 没有only, 计算需要的字段: (_db_field_map | includes) - excludes
            expected = set([f for f in self])

        packed = {}
        for field in expected:
            # 只返最后一笔交易(如有)
            if field == 'transact_list' and hasattr(self, field) and self[field]:
                packed[field] = self[field][-1]
            else:
                value = self[field] if hasattr(self, field) else None
                packed[field] = Call._field_to_json(value)
        return packed


class Express(Document):
    """
    Model for Express.
    """
    number = StringField(min_length=12, max_length=12, unique=True, comment='12位单号, 要求唯一')
    third_party = DictField(default=None, comment='第三方运单来源: name, order_id')
    status = DictField(default=dict(status='CREATED', sub_status='CREATED'),
                       comment='运单状态: status: [PER_CREATED/CREATED/SENDING/FINISHED],'
                               'sub_status: [PER_CREATED/CREATED/SENDING,DELAY/FINISHED,NO_CASH,CANCEL,TRASH,REFUSE]')
    creator = DictField(default=dict, comment='id, name, tel, m_type: 其中m_type为角色,暂时记录app-name')

    assignee = DictField(default=None, comment='持有人, 可以(转交,妥投/异常): id, name, tel, m_type, need_zj')
    candidates = ListField(default=list, comment='下一个持有人候选: [{id, name, tel, m_type, need_zj}]')
    occupant = DictField(default=dict, comment='占坑人{id, name, tel, m_type, need_zj}, 用于抢单: 抢到后,可以看到QJ入口')
    # todo del me
    watchers = ListField(default=None, comment='关注人: [{id, name, tel, m_type}]')

    node = DictField(default=dict(node_n={}, node_0={}),
                     comment='node_n是送达信息;node_0是取货信息. '
                             '形如: name, tel, loc{name,addr,lat,lng}, fence{id,name,node{id,name,loc}}...')
    fee = DictField(default=dict, comment='fh, ps...')

    times = DictField(comment='driver_qj_time, man_qj_time...')
    create_time = DateTimeField(default=utc_now, comment='创建时间')
    update_time = DateTimeField(default=utc_now, comment='更新时间')

    remark = StringField(default="", max_length=128, comment='运单备注')

    meta = {
        'db_alias': 'aeolus_connection',
        'collection': 'express',
        'ordering': [
            '-update_time',
        ],
        'indexes': [
            'status.status',
            'status.sub_status',
            'assignee.id',
            'candidates.id',
            'occupant.id',
            'node.node_n.tel',
            # 'create_time',
            'update_time'
        ]
    }

    @classmethod
    @gen.coroutine
    def create(cls, creator, **kwargs):
        def is_third_party(third_party):
            if not third_party:
                return False
            if third_party.get('order_id'):
                return True
            return False

        # 如果是第三方订单, 则先查看是否已经创建
        third_party = kwargs.get('third_party')
        if is_third_party(third_party):
            order_id = third_party['order_id']
            name = third_party['name']
            query = Q(third_party__order_id=order_id)
            if name:
                query &= Q(third_party__name=name)

            expr = Express.objects(query).first()

            if expr:
                # 第三方订单存在并且是这个商户的订单, 则返回否则创建失败
                if expr.creator['id'] == creator['id']:
                    raise gen.Return(expr)
                else:
                    raise DuplicateDocError()

        number = kwargs.pop("number", None)
        if number is None:
            # 生成运单流水号
            number = yield generate_number()
            if number is None:
                raise ApiError("获取运单流水号失败")

        # 创建新的运单
        expr = Express(
            number=number,
            creator=creator,
            **kwargs
        ).save()
        expr.reload()
        raise gen.Return(expr)

    @property
    def trace(self):
        trace_list = Trace.objects(number=self.number)
        return [trace for trace in trace_list]

    @property
    def last_trace(self):
        trace = Trace.objects(number=self.number).order_by("-create_time").first()
        return trace

    def update(self, **kwargs):
        kwargs.update({"set__update_time": utc_now()})
        return super(Express, self).update(**kwargs)

    def modify(self, **kwargs):
        kwargs.update({"set__update_time": utc_now()})
        return super(Express, self).modify(**kwargs)

    def save(self, **kwargs):
        self.update_time = utc_now()
        return super(Express, self).save(**kwargs)

    @classmethod
    def filter_expr(cls, kw, excludes=(), includes=(), only=()):
        includes = ('set__node__node_n', 'set__third_party__name') if not includes else includes
        expected = only
        if not expected:
            # 有only只返回only; 没有only, 计算需要的字段: _db_field_map | includes - excludes
            expected = (set(cls._db_field_map) | set(includes)) - set(excludes)
        filtered = {}
        for k in expected:
            if k in kw:
                filtered[k] = kw[k]
        return filtered

    @staticmethod
    def _field_to_json(value):
        ret = value
        if isinstance(value, ObjectId):
            ret = safe_unicode(str(value))
        elif isinstance(value, datetime):
            ret = utc_to_local(value)
        elif isinstance(value, EmbeddedDocument):
            if hasattr(value, "pack"):
                ret = value.pack()
        elif isinstance(value, Document):
            if hasattr(value, "pack"):
                ret = value.pack()
            else:
                ret = safe_unicode(value.pk)
        elif isinstance(value, list):
            ret = [Express._field_to_json(_) for _ in value]
        elif isinstance(value, dict):
            ret = {k: Express._field_to_json(v) for k, v in value.iteritems()}
        elif isinstance(value, float):
            ret = round(ret, 10)
        return ret

    def pack(self, excludes=(), includes=(), only=()):
        # 有可能传None进来,set(None)会报错
        excludes = excludes if excludes else ()
        includes = includes if includes else ()
        only = only if only else ()

        expected = only
        if not only:
            # 有only只返回only; 没有only, 计算需要的字段: _db_field_map | includes - excludes
            expected = (set([f for f in self]) | set(includes)) - set(excludes)

        packed = {}
        for field in expected:
            if field == 'trace':
                value = self.trace
            elif field == 'last_trace':
                value = self.last_trace
            else:
                value = self[field] if hasattr(self, field) else None
            packed[field] = Express._field_to_json(value)
        return packed


class Trace(Document):
    """
    Trace for Express.
    """
    number = StringField(min_length=12, max_length=12, comment='12位单号')
    from_status = StringField(max_length=32, comment='从哪个状态, 对应于Express.status.sub_status')
    to_status = StringField(max_length=32, comment='变为哪个状态, 对应于Express.status.sub_status')
    event = StringField(max_length=32, comment='触发事件: ')
    event_source = StringField(max_length=16, comment='事件来源: INSIDE或OUTSIDE')

    # 操作人(operating_loc操作人操作轨迹的时候所在的地理位置信息, lat, lng, addr)
    operator = DictField(default=dict, max_length=24, comment='操作人: id, name, tel, m_type, operating_loc')
    msg = StringField(default=None, max_length=128, comment='操作备注;APP端显示的通知内容;')

    create_time = DateTimeField(default=utc_now, comment='创建时间')

    meta = {
        'db_alias': 'aeolus_connection',
        'collection': 'trace',
        'ordering': [
            '-create_time',
        ],
        'indexes': [
            'number',
        ]
    }

    def pack(self):
        packed = {}
        for field in self:
            if field == 'id':
                continue
            value = self[field]
            packed[field] = Express._field_to_json(value)
        return packed


class ClientAddress(Document):
    client = DictField(default=dict, comment='客户信息: id, name, tel, client_id')

    default = DictField(default=dict, comment='默认发货地址: name, tel, lat,lng,address')
    node_0 = ListField(default=list, comment='发货地址库: [{name, tel, lat,lng,address},...]')
    node_n = ListField(default=list, comment='送达地址库: [{name, tel, lat,lng,address},...]')

    create_time = DateTimeField(default=utc_now, comment='创建时间')
    update_time = DateTimeField(default=utc_now, comment='更新时间')

    meta = {
        'db_alias': 'aeolus_connection',
        'collection': 'address',
        'ordering': [
            '-update_time',
        ],
        'indexes': [
            'client.id',
            'client.name',
            'client.tel',
            'default.name',
            'default.tel',
            'default.loc.address',
        ]
    }

    def pack(self):
        return {
            "client": self.client,
            "default": self.default,
            "node_0": self.node_0,
            "node_n": self.node_n
        }
