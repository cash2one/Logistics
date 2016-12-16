# coding:utf-8
import logging
from decimal import Decimal
from models import Statistics, Flow, TopUp, Shop, ShopFSMLog, TRANSACT_TYPE
from tools_lib.transwarp.tz import utc_8_now
from tools_lib.transwarp.validate import is_valid_kw
from tools_lib.transwarp.web import Dict
from tools_lib.transwarp import db


class ShopFSMLogLogic(object):
    """
    Model logic for ShopFSMLog.
    """

    @staticmethod
    def create(**kw):
        # 参数合法性检查. 如果不合法,直接报错.
        is_valid_kw(ShopFSMLog, **kw)
        now = utc_8_now()
        kw['create_time'] = kw.get('create_time', now)
        shop_fsm_log = ShopFSMLog(**kw)
        shop_fsm_log.insert()

    @staticmethod
    def find_by(cols, where, limit, *args):
        """
        :param str cols: "shop_id, to_status"/"*"
        :param str where: "where event REGEXP BINARY ? AND NOT from_status=?"
        :param str limit: "order by id limit 50"
        :param list args: list of args to fill into the generated sql params.
        :return: [{}]
        """
        where = "%s %s" % (where, limit) if where else limit
        return ShopFSMLog.find_by(cols, where, *args)


class ShopLogic(object):
    """
    Model logic for Shop.
    """

    @staticmethod
    def filter_shop(kw, excludes=(), includes=()):
        s_filtered = Dict()
        for key in Shop._db_field_map:
            if key in kw and key not in excludes:
                s_filtered[key] = kw[key]
        for key in includes:
            if key in kw:
                s_filtered[key] = kw[key]
        return s_filtered

    @staticmethod
    def pack_shop(s, excludes=None, includes=None, only=None):
        # 有可能传None进来,set(None)会报错
        excludes = excludes if excludes else ('password',)
        includes = includes if includes else ()
        only = only if only else ()

        expected = only
        if not only:
            # 如果only为空, 不返回 excludes, 额外返回 includes
            expected = (set(Shop._db_field_map) | set(includes)) - set(excludes)

        s_packed = Dict()
        # 有only只返回only; 没有only, 计算需要的字段: _db_field_map | includes - excludes
        for key in s:
            if key in expected:
                if key == 'id':
                    s_packed['shop_id'] = unicode(s[key])
                else:
                    s_packed[key] = s[key]
        return s_packed


class TopUpLogic(object):
    @staticmethod
    def create(**kw):
        is_valid_kw(TopUp, **kw)
        kw['create_time'] = utc_8_now()
        tu = TopUp(**kw)
        tu.insert()

    @staticmethod
    def find_first(cols, where, *args):
        return TopUp.find_first(cols, where, *args)


class FlowLogic(object):
    # 返回可能的状态们
    MSGS = Dict(**{x: x for x in ('notify_first_success', 'notify_duplicated_success', 'notify_failure')})

    @staticmethod
    def found_rows(cols, where='', *args):
        # where = "%s %s" % (where, limit) if where else limit
        return Flow.found_rows(cols, where, *args)

    @staticmethod
    def find_by(cols, where='', limit='', *args):
        """
        :param str cols: "shop_id, status"/"*"
        :param str where: "where status REGEXP BINARY ? AND NOT cash=?"
        :param str limit: "order by id limit 2*50, 50"
        :param list args: list of args to fill into the generated sql params.
        :return: [{}]
        """
        where = "%s %s" % (where, limit) if where else limit
        return Flow.find_by(cols, where, *args)

    @staticmethod
    @db.with_transaction
    # 支付成功: 记录flow_top_up.result; 记录PAY流水(添加remark: 微信支付/支付宝支付/余额支付);
    def transfer_success(**kw):
        # 输入kw: result, transact_num, trade_no, remark
        logging.info('transfer_success, kw=%s' % kw)

        transact_num = kw['transact_num']
        # 0. 已经收到过该通知,直接返回;
        flow = Flow.find_first('*', 'where transact_num=?', transact_num)
        if flow:
            logging.info("Already received notification for transact_num=[%s]." % transact_num)
            return FlowLogic.MSGS.notify_duplicated_success
        # 1. 记录flow_top_up.result;
        top_up_flow = TopUp.find_first('*', 'where transact_num=?', transact_num)
        top_up_flow.result = kw['result']
        top_up_flow.trade_no = kw['trade_no']
        top_up_flow.update()
        kw['shop_id'] = top_up_flow.shop_id

        # 根据flow_top_up, 从shop_id拿name, tel, 不会真正去查商户数据库
        shop_id = top_up_flow.shop_id
        kw['shop_name'] = top_up_flow.shop_name
        kw['shop_tel'] = top_up_flow.shop_tel

        kw['create_time'] = utc_8_now()
        kw['cash'] = round(Decimal(top_up_flow.cash), 2)
        kw['type'] = TRANSACT_TYPE.PAY
        cash = kw['cash']
        # 2. 增加消费;
        stat = Statistics.find_first('*', 'where shop_id=?', shop_id)
        if not stat:
            stat = Statistics(shop_id=shop_id, shop_name=kw['shop_name'], expense=cash)
            kw['balance'] = 0
            stat.insert()
        else:
            stat.expense = round((Decimal(stat.expense) + Decimal(cash)), 2)  # 计算[消费]
            kw['balance'] = stat.balance
            stat.update()

        # 3. 记录流水: 流水中还要记入这次操作后的balance.
        flow = Flow(**kw)
        flow.insert()
        return FlowLogic.MSGS.notify_first_success

    @staticmethod
    @db.with_transaction
    # 充值成功: 记录flow_top_up.result; 增加余额; 记录流水;
    def top_up_success(**kw):
        # 输入kw: result, transact_num, trade_no
        logging.info('top_up_success, kw=%s' % kw)
        transact_num = kw['transact_num']
        # 0. 已经收到过该通知,直接返回;
        flow = Flow.find_first('*', 'where transact_num=?', transact_num)
        if flow:
            logging.info("Already received notification for transact_num=[%s]." % transact_num)
            return FlowLogic.MSGS.notify_duplicated_success
        # 1. 记录flow_top_up.result;
        top_up_flow = TopUp.find_first('*', 'where transact_num=?', transact_num)
        top_up_flow.result = kw['result']
        top_up_flow.trade_no = kw['trade_no']
        top_up_flow.update()
        kw['shop_id'] = top_up_flow.shop_id

        # 根据flow_top_up, 从shop_id拿name, tel, 不会真正去查商户数据库
        shop_id = top_up_flow.shop_id
        kw['shop_name'] = top_up_flow.shop_name
        kw['shop_tel'] = top_up_flow.shop_tel

        kw['create_time'] = utc_8_now()
        kw['cash'] = round(Decimal(top_up_flow.cash), 2)
        kw['type'] = TRANSACT_TYPE.TOP_UP
        cash = kw['cash']
        # 2. 增加余额;
        stat = Statistics.find_first('*', 'where shop_id=?', shop_id)
        if not stat:
            stat = Statistics(shop_id=shop_id, shop_name=kw['shop_name'], balance=cash)
            kw['balance'] = cash
            stat.insert()
        else:
            stat.balance = round((Decimal(stat.balance) + Decimal(cash)), 2)  # 计算[余额]
            kw['balance'] = stat.balance
            stat.update()

        # 3. 记录流水: 流水中还要记入这次操作后的balance.
        flow = Flow(**kw)
        flow.insert()
        return FlowLogic.MSGS.notify_first_success

    @staticmethod
    # 充值/转账支付失败: 记录flow_top_up.result
    def notified_of_failure(**kw):
        logging.info('top_up_failure, kw=%s' % kw)
        transact_num = kw['transact_num']
        # 先检查是否该笔transact_num已经成功过
        flow = Flow.find_first('*', 'where transact_num=?', transact_num)
        if flow:
            logging.error("Flow with transact_num=[%s] already succeeded, can't fail it now." % transact_num)
            return FlowLogic.MSGS.notify_failure
        # 没成功过,记录失败通知.
        top_up_flow = TopUp.find_first('*', 'where transact_num=?', transact_num)
        # 该笔记录是否失败过
        if top_up_flow.result:
            return FlowLogic.MSGS.notify_failure
        top_up_flow.result = kw['result']
        top_up_flow.trade_no = kw['trade_no']
        top_up_flow.update()
        return FlowLogic.MSGS.notify_failure

    @staticmethod
    @db.with_transaction
    # 扣费: 减少余额; 增加消费; 记录流水;
    def deduct(**kw):
        # todo: 不要从shop_id拿name, tel, 商户信息改从参数传入
        shop_id = kw['shop_id']
        shop = Shop.objects(id=shop_id).first()
        if not shop:
            raise ValueError("No such shop=[%s]." % shop_id)
        kw['shop_name'] = shop.name if shop.name else ""
        kw['shop_tel'] = shop.tel if shop.tel else ""

        kw['type'] = TRANSACT_TYPE.PAY
        kw['cash'] = round(Decimal(kw['cash']), 2)
        cash = kw['cash']
        kw['create_time'] = utc_8_now()

        # 1. 减少余额; 增加消费;
        stat = Statistics.find_first('*', 'where shop_id=?', shop_id)
        if not stat:
            raise ValueError(
                "Trying to deduct non-existed/haven't topped up shop with id=[%s], please register or top up first." % shop_id)
        else:
            stat.balance = round((Decimal(stat.balance) - Decimal(cash)), 2)
            if stat.balance < 0:
                raise ValueError("Shop with id=[%s] will have minus balance after deduction of [%s]." % (shop_id, cash))
            kw['balance'] = stat.balance
            stat.expense = round((Decimal(stat.expense) + Decimal(cash)), 2)
            stat.update()
        # 2. 记录流水: 流水中还要记入这次操作后的balance.
        flow = Flow(**kw)
        flow.insert()
        return flow.transact_num

    @staticmethod
    @db.with_transaction
    # 退款: 增加余额; 减少消费; 记录流水;
    def refund(**kw):
        # todo: 不要从shop_id拿name, tel, 商户信息改从参数传入
        shop_id = kw['shop_id']
        shop = Shop.objects(id=shop_id).first()
        if not shop:
            raise ValueError("No such shop=[%s]." % shop_id)
        kw['shop_name'] = shop.name if shop.name else ""
        kw['shop_tel'] = shop.tel if shop.tel else ""

        kw['type'] = TRANSACT_TYPE.REFUND
        kw['cash'] = round(Decimal(kw['cash']), 2)
        cash = kw['cash']
        kw['create_time'] = utc_8_now()

        # 1. 增加余额; 减少消费;
        stat = Statistics.find_first('*', 'where shop_id=?', shop_id)
        if not stat:
            raise ValueError(
                "Trying to refund non-existed/haven't topped up shop with id=[%s], please register or top up first." % shop_id)
        else:
            stat.balance = round(Decimal(stat.balance) + Decimal(cash), 2)
            stat.expense = round(Decimal(stat.expense) - Decimal(cash), 2)
            if stat.expense < 0:
                raise ValueError("Shop[%s] will have minus expense after refund of [%s]." % (shop_id, cash))
        kw['balance'] = stat.balance
        stat.update()

        # 2. 记录流水: 流水中记入这次操作后的balance
        flow = Flow(**kw)
        flow.insert()
        return flow.transact_num


class FlowStatisticsLogic(object):
    @staticmethod
    def find_by(cols, where, limit, *args):
        """
        :param str cols: "shop_id, status"/"*"
        :param str where: "where status REGEXP BINARY ? AND NOT cash=?"
        :param str limit: "order by id limit 2*50, 50"
        :param list args: list of args to fill into the generated sql params.
        :return: [{}]
        """
        where = "%s %s" % (where, limit) if where else limit
        return Statistics.find_by(cols, where, *args)
