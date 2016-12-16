# coding:utf-8
from __future__ import unicode_literals

import datetime
import logging
import time

from fsm_expr import ExprFSM
from models import Call, Express
from schema import Schema, Optional
from tools_lib.bl_call import CallState
from tools_lib.bl_expr import ExprState
from tools_lib.common_util.third_party.sms_api import async_send_sms
from tools_lib.gtornado.apis import get_fee
from tools_lib.gtornado.apis import shop_wxpay_code_url, shop_alipay_code_url
from tools_lib.gtornado.escape import schema_unicode_empty, schema_unicode, schema_float, schema_float_2
from tools_lib.pricing import DEFAULT_CATEGORY
from tornado.gen import Return, coroutine


# == 以下为call, trace信息修改: 请注意输入,输出定义必须完全一致; 错误信息必须由ValueError抛出去. ==
@coroutine
def _add_expr(kwargs, call, operator):
    """
    加单
    :param kwargs:
    :param call:
    :param operator:
    :return:
    """
    kwargs = Schema({
        'name': schema_unicode_empty,
        'tel': schema_unicode,

        'address': schema_unicode_empty,
        'lat': schema_float,
        'lng': schema_float,
        'fence': {
            'id': schema_unicode,
            'name': schema_unicode_empty,
            'node': object
        },

        Optional('category', default=DEFAULT_CATEGORY): schema_unicode,
        Optional('remark', default=''): schema_unicode_empty,
    }).validate(kwargs)
    # 0. 拼一些信息
    creator = {
        'id': call.shop_id,
        'name': call.shop_name,
        'tel': call.shop_tel,
        'm_type': ''
    }
    node = {
        "node_0": {
            "name": call.shop_name,
            "tel": call.shop_tel,
            "addr": call.loc['address'],
            "lat": call.loc['lat'],
            "lng": call.loc['lng'],
            "fence": call.loc['fence']
        },
        "node_n": {
            "name": kwargs['name'],
            "tel": kwargs['tel'],
            "addr": kwargs['address'],
            "lat": kwargs['lat'],
            "lng": kwargs['lng'],
            "fence": kwargs['fence']
        }
    }
    # 1. 预先设置默认运费
    fee = yield get_fee(call.shop_id, kwargs['category'])
    # 2. 状态预设
    status = dict(status=ExprState.STATUS_PRE_CREATED, sub_status=ExprState.SUB_STATUS_PRE_CREATED)
    # 3. 创建
    expr = yield Express.create(
        creator=creator,
        status=status, node=node, remark=kwargs['remark'], fee=fee,
        assignee=operator  # 代商户下单预设领取人为 进行这个操作的派件员
    )
    kwargs['add_to_set__number_list'] = expr.number
    raise Return(kwargs)


@coroutine
def _pay_check(kwargs, call, operator):
    """
    发起收款: 获取微信/支付宝收款二维码
        1. 改f_shop.flow_top_up
        2. 增加aeolus.call的transact_list[ {transact_num,cash,number_list,code_url,  trade_no} ]
        注意: 回调的部分, 要根据transact_num
            改flow_top_up,flow,flow_statistics;
            改aeolus.call.transact_list的trade_no;
            改aeolus.express对应于number_list里面的运单的状态们.
    :param kwargs:
    :param call:
    :param operator:
    :return:
    """
    kwargs = Schema({
        'cash': schema_float_2,
        'number_list': [
            schema_unicode
        ],
        "pay_type": schema_unicode,  # WXPAY/ALIPAY
    }).validate(kwargs)
    # 0.1 想要发起的收款金额必须大于0
    if kwargs['cash'] <= 0:
        raise ValueError('总计发起收款的金额必须大于0元')
    # 0.2 信息校验
    cash = Express.objects(
        number__in=kwargs['number_list'],  # 传入的这些单
        assignee__id=operator['id'],  # 是配送员领取/代填写的单
        creator__id=call.shop_id,  # 是该商户下的单
        status__sub_status=ExprState.SUB_STATUS_PRE_CREATED,  # 必须都没被别人发起过收款(PRE_CREATED.PRE_CREATED)
        node__node_n__tel={"$exists": True, "$ne": ""},  # 都填过收方信息了
        fee__fh={"$exists": True, "$ne": None}
    ).aggregate_sum('fee.fh')
    if cash == 0:
        raise ValueError("运单校验失败, 请尝试刷新页面后重试")
    elif round(cash, 2) != kwargs['cash']:
        raise ValueError("运单和运费校验失败, 请尝试刷新页面或单笔付款")

    # 1. 信息校验成功, 向DAS-shop请求记录支付操作, 同时向微信发起NATIVE类型的预交易请求
    if kwargs['pay_type'] == 'WXPAY':
        ret = yield shop_wxpay_code_url(call.shop_id, call.shop_name, call.shop_tel, kwargs['cash'])
    elif kwargs['pay_type'] == 'ALIPAY':
        ret = yield shop_alipay_code_url(call.shop_id, call.shop_name, call.shop_tel, kwargs['cash'])
    else:
        logging.error('pay_type[%s] should be either WXPAY or ALIPAY.' % kwargs['pay_type'])
        raise ValueError('未知支付类型')
    # 2. 增加aeolus.call的transact_list[ {transact_num,cash,number_list,code_url,  trade_no} ]
    if ret:
        kwargs = {
            'push__transact_list': {
                'transact_num': ret['transact_num'],
                'cash': kwargs['cash'],
                'number_list': kwargs['number_list'],
                'code_url': ret['code_url'],
            }}
        raise Return(kwargs)
    else:
        # 在前面应该有error log.
        raise ValueError('向微信/支付宝发起预交易请求失败, 请稍后重试')


def _sj(kwargs, call, operator):
    """
    收件
    :param kwargs:
    :param call:
    :param operator:
    :return:
    """
    kwargs = Schema({
        'number': schema_unicode
    }).validate(kwargs)
    number = kwargs['number']

    if number not in set(call.number_list):
        raise ValueError('该运单不属于本次呼叫, 请核对后到对应呼叫入口内扫码收件')

    expr = Express.objects(number=number).first()
    if not expr:
        raise ValueError('找不到对应的运单')

    # ==> 运单事件
    # 0. 错误预判
    status = expr.status['status']
    err = {
        (ExprState.STATUS_PRE_CREATED, ExprState.EVENT_SJ): '收件失败, 该运单未付款',
        (ExprState.STATUS_SENDING, ExprState.EVENT_SJ): '收件失败, 该运单已被收件',
        (ExprState.STATUS_FINISHED, ExprState.EVENT_SJ): '收件失败, 该运单已完结',
    }
    msg = err.get((status, ExprState.EVENT_SJ))
    if msg:
        raise ValueError(msg)

    # 1. 统一处理事件:
    # FSM 调用状态机
    try:
        modified_expr = ExprFSM.update_status('OUTSIDE', expr, ExprState.EVENT_SJ, operator, **kwargs)
    except ValueError as e:
        logging.warn(
            'State transfer for expr[%s][%s] using [%s] failed.' % (expr.number, expr.status, ExprState.EVENT_SJ))
        logging.exception(e)
        raise ValueError(e.message)
    else:
        return {}  # 啥信息都不用改


def _cancel(kwargs, call, operator):
    """
    派件员取消运单
    :param kwargs:
    :param call:
    :param operator:
    :return:
    """
    kwargs = Schema({
        'number': schema_unicode
    }).validate(kwargs)
    number = kwargs['number']
    if number not in set(call.number_list):
        raise ValueError('该运单不属于本次呼叫, 请核对后到对应的呼叫入口内取消此件')

    expr = Express.objects(number=number).first()
    if not expr:
        raise ValueError('找不到对应的运单')
    # ==> 运单事件
    # 0. 错误预判
    status = expr.status['status']
    err = {
        (ExprState.STATUS_CREATED, ExprState.EVENT_CANCEL): '取消失败, 该运单已付款',
        (ExprState.STATUS_SENDING, ExprState.EVENT_CANCEL): '取消失败, 该运单已被收件',
        (ExprState.STATUS_FINISHED, ExprState.EVENT_CANCEL): '取消失败, 该运单已完结',
    }
    msg = err.get((status, ExprState.EVENT_CANCEL))
    if msg:
        raise ValueError(msg)
    # 1. 统一处理运单事件
    # FSM 调用状态机
    try:
        modified_expr = ExprFSM.update_status('OUTSIDE', expr, ExprState.EVENT_CANCEL, operator, **kwargs)
    except ValueError as e:
        logging.warn('运单[%s][%s]状态变迁失败: 操作[%s].' % (expr.number, expr.status, ExprState.EVENT_CANCEL))
        logging.exception(e)
        raise ValueError(e.message)
    else:
        return {}  # 啥信息都不用改


# == 检查入口是否可以关闭 ==
def _all_sending_or_cancel(call):
    # 该次呼叫的单(如有), 是否都进入配送/取消的状态.
    expr_query_set = Express.objects(number__in=call.number_list).only('status')
    for expr in expr_query_set:
        if expr['status']['status'] in (ExprState.STATUS_SENDING, ExprState.STATUS_FINISHED):
            continue
        else:
            # 还有挂着的单, 入口不能关闭.
            return False
    # 没任何单/都进入了完结态, 则可关闭.
    return True


# == 以下为短信通知 ==
def _will_come(call, msg, operator):
    async_send_sms(call['shop_tel'],
                   '您已呼叫成功，收件员%s %s 即将上门，请耐心等待。' % (operator.get('name', ''), operator.get('tel', '')))


class CallFSM(CallState):
    """
    一键呼叫有限状态机
    """
    # === 呼叫状态 ===
    # 主状态
    STATUS_ALL = 'ALL'
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_BE_IN_PROCESS = 'BE_IN_PROCESS'
    STATUS_CLOSABLE = 'CLOSABLE'
    STATUS_CLOSED = 'CLOSED'
    # STATUS_FORWARDING = 'FORWARDING'
    # STATUS_FORWARD_OK = 'FORWARD_OK'
    # STATUS_FORWARD_FAIL = 'FORWARD_FAIL'

    # === 呼叫状态转换事件 ===
    # 后台上帝操作: 将单变成初始状态
    EVENT_RESET = 'EVENT_RESET'
    # 抢呼叫
    EVENT_ASSIGN_TO_ME = 'EVENT_ASSIGN_TO_ME'
    # 加单
    EVENT_ADD = 'EVENT_ADD'
    # 发起收款: 获取微信/支付宝收款二维码
    EVENT_PAY_US = 'EVENT_PAY_US'
    # 收件
    EVENT_SJ = 'EVENT_SJ'
    # 取消
    EVENT_CANCEL = 'EVENT_CANCEL'
    # 关闭呼叫入口
    EVENT_CLOSE = 'EVENT_CLOSE'
    # 转交
    # EVENT_ZJ = 'EVENT_ZJ'
    # EVENT_ACCEPT = 'EVENT_ACCEPT'
    # EVENT_REJECT = 'EVENT_REJECT'

    # === 状态转换字典, 元素结构: (初始状态，条件): 下一个状态 ===
    FSM = {
        'OUTSIDE': {
            # [APP] 抢呼叫
            (STATUS_ALL, EVENT_ASSIGN_TO_ME): {'next': STATUS_ASSIGNED, 'sms': _will_come},
            # [APP] 关闭呼叫入口
            (STATUS_ASSIGNED, EVENT_CLOSE): {'next': STATUS_CLOSED},
            # [APP] 转交
            # (STATUS_ASSIGNED, EVENT_ZJ): {'next': STATUS_FORWARDING},
            # (STATUS_FORWARDING, EVENT_ACCEPT): {'next': STATUS_FORWARD_OK},
            # (STATUS_FORWARDING, EVENT_REJECT): {'next': STATUS_FORWARD_FAIL},
            # [APP] 加单
            # (STATUS_FORWARD_OK, EVENT_ADD): {'do': _add_expr, 'next': STATUS_BE_IN_PROCESS},
            (STATUS_ASSIGNED, EVENT_ADD): {'do': _add_expr, 'next': STATUS_BE_IN_PROCESS},
            (STATUS_BE_IN_PROCESS, EVENT_ADD): {'do': _add_expr, 'next': STATUS_BE_IN_PROCESS},
            # [APP] 发起收款
            (STATUS_BE_IN_PROCESS, EVENT_PAY_US): {'do': _pay_check, 'next': STATUS_BE_IN_PROCESS},
            # [APP] 取消: 没单, 不能对这次呼叫取消
            (STATUS_BE_IN_PROCESS, EVENT_CANCEL): {'do': _cancel, 'cond': _all_sending_or_cancel,
                                                   'next': STATUS_CLOSABLE},
            # [APP] 收件: 没单, 不能对这次呼叫收件
            (STATUS_BE_IN_PROCESS, EVENT_SJ): {'do': _sj, 'cond': _all_sending_or_cancel, 'next': STATUS_CLOSABLE},
            (STATUS_ASSIGNED, EVENT_SJ): {'do': _sj, 'cond': _all_sending_or_cancel, 'next': STATUS_CLOSABLE},
            # [APP] 加单
            (STATUS_CLOSABLE, EVENT_ADD): {'do': _add_expr, 'next': STATUS_BE_IN_PROCESS},
            # [APP] 关闭呼叫入口
            (STATUS_CLOSABLE, EVENT_CLOSE): {'next': STATUS_CLOSED},
        },
        'INSIDE': {
            # [后台]上帝操作, 将单变成初始状态
            # (*, EVENT_RESET): *,

            # [后台]万能修改,不改状态
            # (*, EVENT_ALTER_INFO): *,
        }
    }
    OUTSIDE_EVENTS = set([e[1] for e in FSM['OUTSIDE'].keys()])
    INSIDE_EVENTS = set([e[1] for e in FSM['INSIDE'].keys()]).union({EVENT_RESET})

    @classmethod
    def get_next_state(cls, operator_type, current_status, event):
        """
        获取下一状态
        :param operator_type: 'OUTSIDE'/'INSIDE'
        :param current_status: 当前状态的主状态
        :param event: 条件
        :return: 如果返回None表示错误状态或条件; 否则返回形如{'next': STATUS_CAN_BE_CLOSED, 'send_sms': '通知信息'}
        """
        fsm = cls.FSM[operator_type]
        # 状态变迁
        next_state_info = fsm.get((current_status, event), None)
        return next_state_info

    @classmethod
    @coroutine
    def update_status(cls, operator_type, call, operation, operator, current_status=None, **kwargs):
        """
        更新对象的状态
        :param operator_type: 'OUTSIDE'/'INSIDE'
        :param call: 运单对象
        :param current_status: 当前状态, 如果为None就拿call的status字段
        :param operation: 运单事件类型
        :param operator: 运单责任人
        :param kwargs: 除去状态, 其他需要修改的信息. 目前支持:
            var_a: info a
            var_b: info b
        :return: (True, call) 或 (False, error_msg)
        """
        if current_status is None:
            current_status = call.status
        next_state = cls.get_next_state(operator_type, current_status, operation)
        next_status = next_state['next'] if next_state else None

        if operator_type == 'INSIDE':
            # ===> 上帝操作!!! <===
            if operation == cls.EVENT_RESET:
                next_status = cls.STATUS_ALL

        # 日志
        debug_str = 'call[%s][%s]: from [%s] to [%s], event[%s].' % (
            str(call.pk), call.shop_name, current_status, next_status, operation)
        logging.info(debug_str) if next_status else logging.warning(debug_str)

        if next_status:
            # ==> 0. 判断是否有多余的call参数要修改, 以及要不要增加/修改运单
            if 'do' in next_state:
                start = time.time()
                kwargs = yield next_state['do'](kwargs, call=call, operator=operator)
                end = time.time()
                logging.info('@@@: [do] = %s' % datetime.timedelta(seconds=(end - start)))
            # ==> 1. 判断是否有是有条件的跳转
            if 'cond' in next_state:
                start = time.time()
                can_jump_to_next = next_state['cond'](call)
                end = time.time()
                logging.info('@@@: [cond] = %s' % datetime.timedelta(seconds=(end - start)))
                # 无法跳转, 但是也不报错.
                if not can_jump_to_next:
                    raise Return(call)
            # ==> 2. 更新状态, 修改相关信息
            kwargs['status'] = next_status

            # 过滤掉不需要的字段
            kw = Call.filter_call(kwargs, excludes=('shop_id', 'shop_name', 'shop_tel', 'count'))
            if kw:
                call.modify(**kw)

            # ==> 事件记录
            msg = kwargs.get('msg', '')

            # ==> 判断是否要发送短信提醒
            if "sms" in next_state:
                next_state['sms'](call, msg=msg, operator=operator)

            raise Return(call)
        else:
            raise ValueError('操作失败')
