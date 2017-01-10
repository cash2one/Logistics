# coding:utf-8


import datetime
import logging
import time

from .models import Express, Trace, ClientAddress, Fence, Node
from tools_lib.bl_expr import ExprState
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.weibo.tools import tiny_url
from tools_lib.common_util.third_party.sms_api import async_send_sms, SMS_TYPE_NORMAL


# == 以下为expr, trace信息修改: 请注意输入,输出定义必须完全一致; 错误信息必须由ValueError抛出去. ==
# == 收件 ==
def _sj(kw, expr, now, operator):
    # 1. 添加times.sj_time, 用来计算收件费用
    kw['times__sj_time'] = now
    # 2. 更新assignee和watchers
    kw['assignee'] = operator
    kw['add_to_set__watchers'] = operator
    # 3. trace的msg加入寄方fence
    m_type = operator['m_type']
    if m_type == "parttime":
        trace_msg = '派件员{name} {tel} 已收件'.format(name=operator['name'], tel=operator['tel'])
    elif m_type == "city_driver":
        trace_msg = '环线司机已收件'
    else:
        trace_msg = '已收件'
    fence = expr.node.get('node_0', {}).get('fence', {})
    if fence and fence.get('name') and fence.get('id') != 'x':
        trace_msg = '[%s] %s' % (fence['name'], trace_msg)
    # 4. 更新下一个持有人候选列表,暂时只考虑3种模式: A收A派, A收B派, A收S车B派
    fence_0 = expr.node['node_0']['fence']
    fence_n = expr.node['node_n']['fence']
    node_0 = fence_0['node']
    node_n = fence_n['node']
    # 发货围栏 == 送达围栏: A收A派
    if fence_0['id'] == fence_n['id']:
        logging.info('运单[%s] 发货围栏[%s] == 送达围栏[%s]: A收A派' % (expr.number, fence_0['name'], fence_n['name']))
        kw['assignee']['need_zj'] = False
        kw['candidates'] = []
    # 发货站点 == 送达站点 and 发货围栏 != 送达围栏: A收B派
    elif node_0['id'] == node_n['id']:
        logging.info('运单[%s] 发货站点[%s] == 送达站点[%s] and 发货围栏[%s] != 送达围栏[%s]: A收B派'
                     % (expr.number, node_0['name'], node_n['name'], fence_0['name'], fence_n['name']))
        kw['assignee']['need_zj'] = True  # 要转交
        # 送达围栏下的派件员B们, B们的need_zj=False
        start = time.time()
        fn = Fence.objects.get(id=fence_n['id'])
        end = time.time()
        logging.info('@@@: [sj-Fence] = %s' % datetime.timedelta(seconds=(end - start)))
        _names, bs = [], []
        if not fn:
            logging.error('运单[%s][A收B派], 找不到送达围栏[%s]' % (expr.number, fence_n['name']))
        elif not fn.mans:
            logging.error('运单[%s][A收B派], 送达围栏[%s]下没有派件员' % (expr.number, fence_n['name']))
        else:
            for m in fn.mans:
                m['need_zj'] = False
                _names.append(m['name'])
            bs = fn.mans
        kw['candidates'] = bs
        logging.info('运单[%s][A收B派], 找到候选派件员B: %s' % (expr.number, ','.join(_names)))
    # 发货站点 != 送达站点: A收S车B派
    else:
        logging.info('运单[%s] 发货站点[%s] != 送达站点[%s]: A收S车B派' % (expr.number, node_0['name'], node_n['name']))
        kw['assignee']['need_zj'] = True  # 要转交
        # 发货站点下的司机S们, S们的need_zj=True
        start = time.time()
        n0 = Node.objects.get(id=node_0['id'])
        end = time.time()
        logging.info('@@@: [sj-Node] = %s' % datetime.timedelta(seconds=(end - start)))
        _sids, _names, ss = set(), [], []
        if not n0:
            logging.error('运单[%s][A收S车B派], 找不到发货站点[%s]' % (expr.number, node_0['name']))
        elif not n0.time_table:
            logging.error('运单[%s][A收S车B派], 发货站点[%s]下没有人' % (expr.number, node_0['name']))
        else:
            for tm in n0.time_table:
                man = tm['man']
                if man['id'] in _sids:
                    continue
                else:
                    man['need_zj'] = True
                    ss.append(man)
                    _names.append(man['name'])
                    _sids.add(man['id'])

            logging.info('运单[%s][A收S车B派], 找到转交人候选S: %s' % (expr.number, ','.join(_names)))
        kw['candidates'] = ss

    return kw, trace_msg


# == 抢单 ==
def _qd(kw, expr, now, operator):
    # 0. 判断是否已经被抢
    occupant = expr.occupant
    assignee = expr.assignee
    if occupant:
        raise ValueError('该件已经被人定下派送, 请刷新列表更新信息哦')
    # 1. 判断抢单人是否在candidates之中
    candidates = expr.candidates
    for c in candidates:
        if operator['id'] == c['id']:
            # 1. 将operator变成occupant, candidates
            kw['occupant'] = c
            kw['candidates'] = [c]
            # 2. 如果(这次抢成功后的)占坑人和持有人是同一个: 抢单操作作为取件操作
            if assignee and c['id'] == assignee['id']:
                expr.occupant = c
                kw, trace_msg = _qj(kw, expr, now, operator)
                return kw, trace_msg
            return kw, None
    logging.error('抢单人[%s]不在运单[%s]交接人候选列表' % (operator['name'], expr.number))
    raise ValueError('您不能抢这单: 如果您是司机, 可能下单时该站点还不在您负责范围内; 如果您是派件员, 那么可能下单时您尚被分配于该围栏')


# == 取件 ==
def _qj(kw, expr, now, operator):
    occupant = expr.occupant
    assignee = expr.assignee
    # 0.1 判断是不是已经被抢了的单(必须存在occupant)
    if not occupant:
        raise ValueError('请先抢到这单, 再取件哦')
    # 0.2 判断取件人是否是occupant
    if operator['id'] != occupant['id']:
        raise ValueError('该件已被别人定下派送,请不要带走哦')
    # 1. 判断是否重复取件: 只有占坑人不等于持有人的时候判断
    if assignee and assignee['id'] != occupant['id'] and expr.assignee.get('id') == operator['id']:
        _number = ' '.join(expr.number[-4:])
        msg = '%s 重复取件' % _number
        logging.warn(msg)
        raise ValueError(msg)
    # 2. 将operator加入assignee和watcher
    kw['assignee'] = occupant
    kw['add_to_set__watchers'] = operator
    # 3. trace里面的msg加入送达fence
    m_type = operator['m_type']
    if m_type == "parttime":
        trace_msg = "派件员{name} {tel} 已取件".format(name=operator['name'], tel=operator['tel'])
    elif m_type == "city_driver":
        trace_msg = "环线司机已取件"
    else:
        trace_msg = '已取件'
    fence = expr.node.get('node_n', {}).get('fence', {})
    if fence and fence.get('name') and fence.get('id') != 'x':
        trace_msg = '[%s] %s' % (fence['name'], trace_msg)
    # 4. 记录转交时间
    if "zj_time" not in expr.times:
        kw['times__zj_time'] = now
    # 5. 更新下一个持有人候选列表: A收B派(B取件), A收S车B派(S取件/B取件)
    fence_n = expr.node['node_n']['fence']
    # S车取件
    if occupant['need_zj']:
        # 送达围栏下的派件员B们, B们的need_zj=False
        fn = Fence.objects(id=fence_n['id']).first()
        _names, bs = [], []
        if not fn:
            logging.error('运单[%s][A收S车B派], 找不到送达围栏[%s]' % (expr.number, fence_n['name']))
        elif not fn.mans:
            logging.error('运单[%s][A收S车B派], 送达围栏[%s]下没有派件员' % (expr.number, fence_n['name']))
        else:
            for m in fn.mans:
                m['need_zj'] = False
                _names.append(m['name'])
            bs = fn.mans
            logging.info('运单[%s][A收S车B派], 找到转交人候选B: %s' % (expr.number, ','.join(_names)))
        kw['candidates'] = bs  # B们将能看到这个单(并去占坑)
    # B派取件
    else:
        logging.info('运单[%s], 交接人B[%s]已取件, 投递中' % (expr.number, occupant['name']))
        kw['candidates'] = []  # A的转交任务将会消失
    # 6. 取完件, 占坑人重新变成空
    kw['occupant'] = {}  # B的取件任务将会消失
    return kw, trace_msg


# == 指派 ==
def _zp(kw, expr, now, operator):
    # 0. 如果没有当前责任人
    if not expr.assignee:
        logging.error('运单[%s]没有当前责任人, 指派失败' % expr.number)
        raise ValueError('指派失败, 请记录下单号[%s]' % expr.number)
    # 1.1 只做派件流程的责任人变更
    kw['assignee'] = operator
    # 1.2 原先需要转交的还是要转, 原先需要妥投的就是妥投
    kw['assignee']['need_zj'] = expr.assignee['need_zj']
    kw['add_to_set__watchers'] = operator
    # 2. trace里面的msg加入送达fence
    trace_msg = '派件员已取件'
    fence = expr.node.get('node_n', {}).get('fence', {})
    if fence and fence.get('name') and fence.get('id') != 'x':
        trace_msg = '[%s] %s' % (fence['name'], trace_msg)
    # 4. 记录转交(责任人变更)时间
    if "zj_time" not in expr.times:
        kw['times__zj_time'] = now
    return kw, trace_msg


# == 转交 ==
def _zj_time(kw, expr, now, operator):
    if "zj_time" not in expr.times:
        kw['times__zj_time'] = now
    return kw, None


# == 异常 ==
def _yc_time(kw, expr, now, operator):
    kw['times__yc_time'] = now
    return kw, None


# == 添加到地址库 ==
def _address(kw, expr, now, operator):
    client = ClientAddress.objects(client__id=expr.creator['id']).first()
    node_0 = expr.node['node_0']
    node_n = expr.node['node_n']
    node_0.pop('fence')
    node_n.pop('fence')
    if not client:
        c = {
            'client': {
                'id': expr.creator['id'],
                'name': expr.creator['name'],
                'tel': expr.creator['tel']
            },
            'default': node_0,  # name, tel, addr, lat, lng, fence={id,name}
            'node_0': [node_0],
            'node_n': [node_n],
        }
        ClientAddress(**c).save()
    else:
        client.modify(add_to_set__node_0=node_0,
                      add_to_set__node_n=node_n,
                      client__name=expr.creator['name'],
                      client__tel=expr.creator['tel'])
    return kw, None


# do不支持输出形式不是(kw, trace_msg)的函数
# def _refund(kw, expr, now, operator):
#     # 主状态pre_created, 直接取消, 不需要退款; 主状态created, 需要退款
#     cost = expr.fee['fh'] + expr.fee['fh_extra']
#     result = yield shop_refund(expr.creator['id'], cost)
#     if not result:
#         logging.exception("@@@: shop[%s] refund[%s] error", expr.creator['id'], cost)


# == 以下为短信通知 ==
def _sj_sms(expr, msg):
    start = time.time()
    shortened_url = tiny_url("http://cha.123feng.com/#/order/list/mobile/%s" % expr.number)
    sms_content = "您好, 您的快件(单号： {number})已由风先生配送, 追踪运单请点击: {url}【风先生】".format(
        number=expr.number,
        url=shortened_url
    )
    async_send_sms(expr["node"]["node_n"]["tel"], sms_content, SMS_TYPE_NORMAL)
    end = time.time()
    logging.info('@@@: [_sj_sms] = %s' % (datetime.timedelta(seconds=(end - start))))


def _tt_sms(expr, msg):
    msg = "您的包裹已妥投，妥投类型：%s，风先生期待再次为您服务！" % (msg if msg else '本人签收')
    async_send_sms(expr['node']['node_n']['tel'], msg, SMS_TYPE_NORMAL)


def _no_cash_sms(expr, msg):
    msg = '很遗憾，您的运单未通过认证%s。' % msg
    async_send_sms(expr.assignee['tel'], msg, SMS_TYPE_NORMAL)


class ExprFSM(ExprState):
    """
    运单有限状态机
    """
    # === 运单状态 ===
    # 主状态
    STATUS_PRE_CREATED = 'PRE_CREATED'
    STATUS_CREATED = 'CREATED'
    STATUS_SENDING = 'SENDING'
    STATUS_FINISHED = 'FINISHED'
    # 主从关联
    STATUS_PRE_CREATED_PRICED = 'PRE_CREATED.PRE_PRICED'
    STATUS_CREATED_CREATED = 'CREATED.CREATED'
    STATUS_SENDING_SENDING = 'SENDING.SENDING'
    STATUS_SENDING_DELAY = 'SENDING.DELAY'
    STATUS_SENDING_WAREHOUSE = 'SENDING.WAREHOUSE'
    STATUS_FINISHED_FINISHED = 'FINISHED.FINISHED'
    STATUS_FINISHED_NO_CASH = 'FINISHED.NO_CASH'
    STATUS_FINISHED_CANCEL = 'FINISHED.CANCEL'
    STATUS_FINISHED_REFUSE = 'FINISHED.REFUSE'
    STATUS_FINISHED_TRASH = 'FINISHED.TRASH'

    # === 运单状态转换事件 ===
    # 后台上帝操作: 将单变成初始状态
    EVENT_RESET = 'EVENT_RESET'
    # 后台拒绝给钱操作: 运单审核不通过/客户投诉
    EVENT_NO_CASH = 'EVENT_NO_CASH'
    # 后台指派
    EVENT_ZP = 'EVENT_ZP'
    # 派件员定价
    EVENT_PRICING = 'EVENT_PRICING'
    # 收件/抢单/取件/入仓操作
    EVENT_SJ = 'EVENT_SJ'
    EVENT_QD = 'EVENT_QD'
    EVENT_QJ = 'EVENT_QJ'
    EVENT_RC = 'EVENT_RC'
    # 发货人取消运单
    EVENT_CANCEL = 'EVENT_CANCEL'
    # 发货人支付
    EVENT_PAY = 'EVENT_PAY'
    # 确认妥投操作
    EVENT_TT = 'EVENT_TT'
    # 延迟派件: 客户要求延迟派件/改地址/要求工作日派件
    EVENT_DELAY = 'EVENT_DELAY'
    # 客户拒收: 商品质量问题/收件人取消/货品有误
    EVENT_REFUSE = 'EVENT_REFUSE'
    # 无法妥投: 地址错误/电话错误/无人接听
    EVENT_TRASH = 'EVENT_TRASH'

    # === 状态转换字典, 元素结构: (初始状态，条件): 下一个状态 ===
    FSM = {
        'OUTSIDE': {
            # [APP/PC/H5] 发货人支付: 因为要支持批量操作, 所以不能在单个运单状态机中表示出来
            # (STATUS_PRE_CREATED, EVENT_PAY): {'next': STATUS_CREATED},
            # [APP/PC/API] 发货人取消/派件员取消
            (STATUS_PRE_CREATED, EVENT_CANCEL): {'next': STATUS_FINISHED_CANCEL},
            # [APP] 扫码或者录单取件
            (STATUS_CREATED, EVENT_SJ): {'next': STATUS_SENDING_SENDING, 'do': _sj, "sms": _sj_sms},
            # [APP/PC/API] 发货人取消 todo: 删除我
            # (STATUS_CREATED, EVENT_CANCEL): {'next': STATUS_FINISHED_CANCEL, 'do': _refund},
            # [APP] 扫码或者录单取件
            (STATUS_SENDING, EVENT_QJ): {'next': STATUS_SENDING_SENDING, 'do': _qj},
            # [APP] 抢单 todo
            (STATUS_SENDING, EVENT_QD): {'next': STATUS_SENDING_SENDING, 'do': _qd},
            # [APP] 入仓
            (STATUS_SENDING, EVENT_RC): {'next': STATUS_SENDING_WAREHOUSE},
            # [APP] 确认妥投
            (STATUS_SENDING, EVENT_TT): {'next': STATUS_FINISHED_FINISHED, 'do': _address, 'sms': _tt_sms},
            # [APP] 延迟派件: 客户要求延迟派件/改地址/要求工作日派件
            (STATUS_SENDING, EVENT_DELAY): {'next': STATUS_SENDING_DELAY, 'do': _yc_time},
            # [APP] 客户拒收: 商品质量问题/收件人取消/货品有误
            (STATUS_SENDING, EVENT_REFUSE): {'next': STATUS_FINISHED_REFUSE, 'do': _yc_time},
            # [APP] 无法妥投: 地址错误/电话错误/无人接听
            (STATUS_SENDING, EVENT_TRASH): {'next': STATUS_FINISHED_TRASH, 'do': _yc_time},
        },
        'INSIDE': {
            # [后台] 判定运单不通过,拒绝给钱
            (STATUS_FINISHED, EVENT_NO_CASH): {'next': STATUS_FINISHED_NO_CASH, 'sms': _no_cash_sms},

            # [后台] 运单指派: 只做派件流程中的持有人变更
            # (STATUS_CREATED, EVENT_ZP): {'next': STATUS_SENDING_SENDING, 'do': _sj, "sms": _sj_sms},
            (STATUS_SENDING, EVENT_ZP): {'next': STATUS_SENDING_SENDING, 'do': _zp},

            # [后台]万能改状态,变成不给钱
            # (*, EVENT_NO_CASH): *,

            # [后台]上帝操作, 将单变成初始状态
            # (*, EVENT_RESET): *,

            # [后台]万能修改,不改状态
            # (*, EVENT_ALTER_INFO): *,
        }
    }
    OUTSIDE_EVENTS = set([e[1] for e in list(FSM['OUTSIDE'].keys())])
    INSIDE_EVENTS = set([e[1] for e in list(FSM['INSIDE'].keys())]).union({EVENT_RESET})

    @classmethod
    def get_next_state(cls, operator_type, current_status, event):
        """
        获取下一状态
        :param operator_type: 'OUTSIDE'/'INSIDE'
        :param current_status: 当前状态的主状态
        :param event: 条件
        :return: 如果返回None表示错误状态或条件; 否则返回形如{'next': STATUS_FINISHED_NO_CASH, 'send_sms': '很遗憾{msg}。'}
        """
        fsm = cls.FSM[operator_type]
        status = current_status['status']
        sub_status = current_status['sub_status']
        # 优先主状态变迁
        next_state_info = fsm.get((status, event), None)
        # 取不到主状态变迁,尝试子状态变迁
        if not next_state_info:
            sub_state = '%s.%s' % (status, sub_status)
            next_state_info = fsm.get((sub_state, event), None)
        return next_state_info

    @classmethod
    def update_status(cls, operator_type, expr, operation, operator, current_status=None, **kwargs):
        """
        更新对象的状态
        :param operator_type: 'OUTSIDE'/'INSIDE'
        :param expr: 运单对象
        :param current_status: 当前状态, 如果为None就拿expr的status字段
        :param operation: 运单事件类型
        :param operator: 运单责任人
        :param kwargs: 除去状态, 其他需要修改的信息. 目前支持:
            var_a: info a
            var_b: info b
        :return: (True, expr) 或 (False, error_msg)
        """
        if current_status is None:
            current_status = expr.status
        next_state = cls.get_next_state(operator_type, current_status, operation)
        next_status = next_state['next'] if next_state else None

        if operator_type == 'INSIDE':
            # ===> 上帝操作!!! <===
            if operation == cls.EVENT_RESET:
                next_status = cls.STATUS_CREATED_CREATED
            # ===> 不给钱操作!!! <===
            elif operation == cls.EVENT_NO_CASH:
                next_status = cls.STATUS_FINISHED_NO_CASH

        # 日志
        debug_str = 'expr[%s]: from [%s] to [%s], event[%s].' % (
            expr.number, current_status['sub_status'], next_status, operation)
        logging.info(debug_str) if next_status else logging.warning(debug_str)

        if next_status:
            start = time.time()
            # ==> 更新状态, 修改相关信息
            from_status = current_status
            status, sub_status = next_status.split('.')
            kwargs['status'] = dict(status=status, sub_status=sub_status)

            # 过滤掉不需要的字段
            kw = Express.filter_expr(kwargs, excludes=('number', 'pkg_id', 'fee', 'watcher', 'assignee'))

            # 事件发生后, 记录操作人的操作时间: 目前只记录EVENT_SJ, EVENT_QJ, EVENT_TT
            time_name = ExprState.build_time_name(operator.get("m_type"), operation)
            now = TimeZone.utc_now()
            if time_name:
                kw["times__" + time_name] = now
            # ==> 判断是否有多余的expr,trace参数要修改
            trace_msg = None
            if next_state and 'do' in next_state:
                s1 = time.time()
                kw, trace_msg = next_state['do'](kw, expr=expr, now=now, operator=operator)
                e1 = time.time()
                logging.info('@@@: [do] = %s' % datetime.timedelta(seconds=(e1 - s1)))

            expr.modify(**kw)

            # ==> 事件记录
            msg = kwargs.get('msg', '')
            fsm_log = dict(number=expr.number,
                           from_status=from_status['sub_status'],
                           to_status=sub_status,
                           event=operation,
                           event_source=expr.third_party.get('name', '') if expr.third_party else '',
                           operator=operator,
                           msg=trace_msg if trace_msg else msg,
                           create_time=now)
            Trace(**fsm_log).save()

            # ==> 判断是否要发送短信提醒
            if "sms" in next_state:
                next_state['sms'](expr, msg=msg)

            end = time.time()
            logging.info('@@@: [expr] = %s' % datetime.timedelta(seconds=(end - start)))
            return expr
        else:
            raise ValueError('操作失败')
