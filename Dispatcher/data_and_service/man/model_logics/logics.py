# coding:utf-8


from decimal import Decimal
from math import floor

from .models import ManFSMLog, Flow, Statistics, CASH_FLOW, Man
from tools_lib.common_util.third_party.image import get_image_url
from tools_lib.transwarp import db
from tools_lib.transwarp.tz import utc_8_now
from tools_lib.transwarp.validate import is_valid_kw
from tools_lib.transwarp.web import Dict, safe_str


class ManFSMLogLogic(object):
    """
    Model logic for DeliverymanFSMLog.
    """

    @staticmethod
    def create(**kw):
        # 参数合法性检查. 如果不合法,直接报错.
        is_valid_kw(ManFSMLog, **kw)
        now = utc_8_now()
        kw['create_time'] = kw.get('create_time', now)
        deliveryman_fsm_log = ManFSMLog(**kw)
        deliveryman_fsm_log.insert()

    @staticmethod
    def find_by(cols, where, group_order_limit, *args):
        """
        :param str cols: "deliveryman_id, to_status"/"*"
        :param str where: "where event REGEXP BINARY ? AND NOT from_status=?"
        :param str group_order_limit: "order by id limit 50"
        :param list args: list of args to fill into the generated sql params.
        :return: [{}]
        """
        where = "%s %s" % (where, group_order_limit) if where else group_order_limit
        return ManFSMLog.find_by(cols, where, *args)


class ManLogic(object):
    """
    Model logic for Man.
    """

    @staticmethod
    def filter_man(kw, excludes=()):
        m_filtered = Dict()
        for key in Man._db_field_map:
            if key in kw and key not in excludes:
                if key == 'id':
                    m_filtered['man_id'] = str(kw[key])
                else:
                    m_filtered[key] = kw[key]
        return m_filtered

    @staticmethod
    def pack_man(m, excludes=(), only=()):
        # 有可能传None进来,set(None)会报错
        excludes = excludes if excludes else ()
        only = only if only else ()

        # 有only只返回only; 没有only, 计算需要的字段: _db_field_map - excludes
        expected = only
        if not only:
            expected = set(Man._db_field_map) - set(excludes)

        m_packed = Dict()
        for key in m:
            if key in expected:
                if key == 'id':
                    m_packed['man_id'] = str(m[key])
                elif key in ('avatar', 'id_card_back'):
                    m_packed[key] = get_image_url(m[key])
                else:
                    m_packed[key] = m[key]
        stuff = ('name', 'avatar')
        for k in stuff:
            # 如果没有这个key
            if k not in m_packed:
                m_packed[k] = ''
            # 或者key在,但是值为空
            elif not m_packed[k]:
                m_packed[k] = ''
        return m_packed


class FlowLogic(object):
    @staticmethod
    def find_by(cols, where, group_order_limit, *args):
        """
        :param str cols: "man_id, status"/"*"
        :param str where: "where status REGEXP BINARY ? AND NOT cash=?"
        :param str group_order_limit: "order by id limit 2*50, 50"
        :param list args: list of args to fill into the generated sql params.
        :return: [{}]
        """
        where = "%s %s" % (where, group_order_limit) if where else group_order_limit
        return Flow.find_by(cols, where, *args)

    # 数据1: 可提现can_cash = VALIDATED - APPLY_WITHDRAW
    # 数据2: 待财务处理finance = APPLY_WITHDRAW - PAID - DECLINE
    # 数据3: 财务已打款paid = PAID
    # 数据4: 财务已拒绝decline = DECLINE
    @staticmethod
    @db.with_transaction
    # 后台已审核的众包运单
    def push_validated(**kw):
        # 参数合法性检查. 如果不合法,直接报错.
        kw['tel'] = ""
        is_valid_kw(Flow, **kw)
        # 1. 重复的运单, 不能通过
        expr_num = kw['expr_num']
        f = Flow.find_first('*', 'where expr_num=?', expr_num)
        if f:
            raise ValueError('Flow with expr_num=[%s] as validated already exists.' % expr_num)

        # 从man_id拿tel
        man_id = kw['man_id']
        man = Man.objects(id=man_id).first()
        if not man:
            raise ValueError("No such man=[%s]." % man_id)
        kw['tel'] = man.tel if man.tel else ""
        # 2. 记录流水
        kw['create_time'] = utc_8_now()
        kw['update_time'] = utc_8_now()
        kw['cash'] = round(Decimal(kw['cash']), 1)
        flow = Flow(**kw)
        # 如果是测试人员,在流水的remark里面记录一下.
        if man.name and safe_str(man.name).find('测试'.encode('utf-8')) != -1:
            flow.remark = '测试'
        elif len(man.accounts) > 0 and safe_str(man.accounts[0]['name']).find('测试'.encode('utf-8')) != -1:
            flow.remark = '测试'
        flow.insert()
        # 3. 增加可提现: 如果是第一次审核通过, 创建flow_statistics记录.
        stat = Statistics.find_first('*', 'where man_id=?', man_id)
        if not stat:
            stat = Statistics(man_id=man_id, can_cash=kw['cash'], finance=0, paid=0, decline=0)
            # 如果是测试人员,在统计表的man_name里面记录一下.
            if man.name and safe_str(man.name).find('测试'.encode('utf-8')) != -1:
                stat.man_name = man.name
            elif len(man.accounts) > 0 and safe_str(man.accounts[0]['name']).find('测试'.encode('utf-8')) != -1:
                stat.man_name = man.accounts[0]['name']
            stat.insert()
        else:
            stat.can_cash = round((Decimal(stat.can_cash) + Decimal(kw["cash"])), 1)  # 计算[可提现]
            stat.update()

    @staticmethod
    @db.with_transaction
    def push_apply_withdraw(**kw):
        # 参数合法性检查. 如果不合法,直接报错.
        kw['tel'] = ""
        is_valid_kw(Flow, **kw)
        # 从man_id拿tel
        man_id = kw['man_id']
        man = Man.objects(id=man_id).first()
        man_tel = man.tel
        kw['tel'] = man_tel if man_tel else ""
        # 限制1: 如果是系统有效全职,不可提现. ==>暂时通过登录来控制
        # 限制2: 限额设为sum(VALIDATED)-sum(APPLY_WITHDRAW)
        man_id = kw['man_id']
        cash = Decimal(kw['cash'])
        # 1. 先floor提现额度到角, 并判断是否超出提现额度.
        kw['cash'] = floor(cash * 10) / 10.0
        cash = Decimal(str(kw['cash']))
        stat = Statistics.find_first('*', 'where man_id=?', man_id)
        if not stat:
            raise ValueError("You have no cash to withdraw.")
        elif stat.can_cash <= 0:
            raise ValueError("You have no cash to withdraw.")
        elif cash <= 0:
            raise ValueError("Why apply for zero or minus value cash?")
        elif cash > stat.can_cash:
            raise ValueError("You are not allowed to apply for cash over [%s] yuan, you are applying [%s]." % (stat.can_cash, cash))
        # 2. 添加提现记录
        kw['create_time'] = utc_8_now()
        kw['update_time'] = utc_8_now()
        flow = Flow(**kw)
        # 如果是测试人员,在流水的remark里面记录一下.
        if man.name and safe_str(man.name).find('测试'.encode('utf-8')) != -1:
            flow.remark = '测试'
        elif len(man.accounts) > 0 and safe_str(man.accounts[0]['name']).find('测试'.encode('utf-8')) != -1:
            flow.remark = '测试'
        flow.insert()
        # 3. 减少可提现; 增加待财务处理; 更新account_name到man_name
        stat.can_cash = round((Decimal(stat.can_cash) - cash), 1)  # 计算[可提现]
        stat.finance = round((Decimal(stat.finance) + cash), 1)  # 计算[待财务处理]
        stat.man_name = kw['account_name'] if kw['account_name'] else stat.man_name
        stat.update()

    @staticmethod
    @db.with_transaction
    def paid(**kw):
        # 参数合法性检查. 如果不合法,直接报错.
        is_valid_kw(Flow, is_update=True, **kw)

        transact_num = kw['transact_num']
        # todo lock on man_id
        flow = Flow.find_first('*', 'where transact_num=?', transact_num)
        if not flow:
            raise ValueError("No cash flow found for transact_num=[%s]." % transact_num)
        man_id = flow.man_id
        # 检查cash, type: flow.cash == cash? flow.type == APPLY_WITHDRAW?
        if round(Decimal(flow.cash), 1) != round(Decimal(kw['cash']), 1):
            raise ValueError("Cash flow for transact_num=[%s] cash amount=[%s], you are trying to pay [%s]." % (
                transact_num, flow.cash, kw['cash']))
        if flow.type != CASH_FLOW.APPLY_WITHDRAW:
            raise ValueError("Cash flow for transact_num=[%s] has been %s." % (transact_num, flow.type))
        flow.type = kw['type']  # 将指定[transact_num]的那条记录的type改成[PAID]
        flow.operator_id = kw['operator_id']  # 将指定[transact_num]的那条记录新增操作人
        flow.update_time = utc_8_now()  # 将指定[transact_num]的那条记录新增操作时间
        flow.update()

        cash = flow.cash  # 从flow表里面拿提现的金额
        stat = Statistics.find_first('*', 'where man_id=?', man_id)
        if not stat:
            raise ValueError("No flow_statistics record found for man_id=[%s]." % man_id)
        stat.finance = round((Decimal(stat.finance) - Decimal(cash)), 1)  # 计算[待财务处理]
        stat.paid = round((Decimal(stat.paid) + Decimal(cash)), 1)  # 计算[已打款]
        stat.update()

    @staticmethod
    @db.with_transaction
    def decline(**kw):
        # 参数合法性检查. 如果不合法,直接报错.
        is_valid_kw(Flow, is_update=True, **kw)

        transact_num = kw['transact_num']
        # todo lock on man_id
        flow = Flow.find_first('*', 'where transact_num=?', transact_num)
        if not flow:
            raise ValueError("No cash flow found for transact_num=[%s]." % transact_num)
        if flow.type != CASH_FLOW.APPLY_WITHDRAW:
            raise ValueError("Cash flow for transact_num=[%s] has been %s." % (transact_num, flow.type))
        man_id = flow.man_id
        # 检查cash, type: flow.cash == cash? flow.type == APPLY_WITHDRAW?
        if round(Decimal(flow.cash), 1) != round(Decimal(kw['cash']), 1):
            raise ValueError("Cash flow for transact_num=[%s] cash amount=[%s], you are trying to decline [%s]." % (
                transact_num, flow.cash, kw['cash']))
        flow.type = kw['type']  # 将指定[transact_num]的那条记录的type改成[DECLINE]
        flow.operator_id = kw['operator_id']  # 将指定[transact_num]的那条记录新增操作人
        flow.remark = kw.get('remark', '')
        flow.update_time = utc_8_now()  # 将指定[transact_num]的那条记录新增操作时间
        flow.update()

        cash = flow.cash
        stat = Statistics.find_first('*', 'where man_id=?', man_id)
        if not stat:
            raise ValueError("No flow_statistics record found for man_id=[%s]." % man_id)
        stat.finance = round((Decimal(stat.finance) - Decimal(cash)), 1)  # 计算[财务待处理]
        stat.decline = round((Decimal(stat.decline) + Decimal(cash)), 1)  # 计算[财务已拒绝]
        stat.update()


class FlowStatisticsLogic(object):
    @staticmethod
    def find_by(cols, where, group_order_limit, *args):
        """
        :param str cols: "man_id, status"/"*"
        :param str where: "where status REGEXP BINARY ? AND NOT cash=?"
        :param str group_order_limit: "order by id limit 2*50, 50"
        :param list args: list of args to fill into the generated sql params.
        :return: [{}]
        """
        where = "%s %s" % (where, group_order_limit) if where else group_order_limit
        return Statistics.find_by(cols, where, *args)
