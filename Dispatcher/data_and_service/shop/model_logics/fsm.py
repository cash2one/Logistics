# coding:utf-8


import logging

from .logics import ShopLogic, ShopFSMLogLogic
from tools_lib.common_util.third_party.sms_api import async_send_sms, SMS_TYPE_NORMAL
from tools_lib.transwarp import db
from tools_lib.transwarp.tz import utc_8_now


class ShopFSM(object):
    """
    商户有限状态机
    """
    # === 商户状态 ===
    # 黑名单
    STATUS_BANNED = 'STATUS_BANNED'
    # 初始状态
    STATUS_INIT = 'STATUS_INIT'
    # 资料已补全
    STATUS_INFO_COMPLETED = 'STATUS_INFO_COMPLETED'
    # 审核已通过
    STATUS_INFO_YES = 'STATUS_INFO_YES'
    # 审核未通过
    STATUS_INFO_NO = 'STATUS_INFO_NO'
    # 有效商户
    STATUS_VALID = 'STATUS_VALID'
    # 无效商户
    STATUS_INVALID = 'STATUS_INVALID'

    # === 商户状态转换事件 ===
    # 后台上帝操作, 重置状态为STATUS_INIT(这样就可以再次完善资料了).
    EVENT_RESET = 'EVENT_RESET'
    # 后台拉黑
    EVENT_BAN = 'EVENT_BAN'
    # 后台资料修改
    EVENT_ALTER_INFO = 'EVENT_ALTER_INFO'
    # OUTSIDE 资料补全
    EVENT_COMPLETE_INFO = 'EVENT_COMPLETE_INFO'
    # 后台人力资料审核通过
    EVENT_HR_DECIDE_YES = 'EVENT_HR_DECIDE_YES'
    # 后台人力资料审核拒绝
    EVENT_HR_DECIDE_INFO_MISTAKEN = 'EVENT_HR_DECIDE_INFO_MISTAKEN'
    # OUTSIDE ack资料审核通过
    EVENT_ACK_INFO_YES = 'EVENT_ACK_INFO_YES'
    # OUTSIDE ack资料审核拒绝
    EVENT_ACK_INFO_NO = 'EVENT_ACK_INFO_NO'

    # === 状态转换字典, 元素结构: (初始状态，条件): 下一个状态 ===
    FSM = {
        'OUTSIDE': {
            # [对外]资料补全 _ 没补全过
            (STATUS_INIT, EVENT_COMPLETE_INFO): {'next': STATUS_INFO_COMPLETED},
            # [对外]资料补全 _ 补全过,没审核过
            (STATUS_INFO_COMPLETED, EVENT_COMPLETE_INFO): {'next': STATUS_INFO_COMPLETED},
            # [对外]ack审核结果 _ 拒绝
            (STATUS_INFO_NO, EVENT_ACK_INFO_NO): {'next': STATUS_INVALID},
            # [对外]ack审核结果 _ 通过
            (STATUS_INFO_YES, EVENT_ACK_INFO_YES): {'next': STATUS_VALID},
        },
        'FE_INSIDE': {
            # [后台]资料审核拒绝,进入审核拒绝
            (STATUS_INFO_COMPLETED, EVENT_HR_DECIDE_INFO_MISTAKEN): {'next': STATUS_INFO_NO,
                                                                     'send_sms': '很遗憾，您提交的资料未通过认证{remark}您可以修改资料并重新提交，感谢您的配合。'},
            # [后台]资料审核通过,进入在岗
            (STATUS_INFO_COMPLETED, EVENT_HR_DECIDE_YES): {'next': STATUS_INFO_YES,
                                                           'send_sms': '恭喜，您的资料已通过认证，现在可以正常下单啦~'},
            # [后台]修改人员资料,不改状态
            # (*, EVENT_ALTER_INFO): *,
        }
    }
    OUTSIDE_EVENTS = set([e[1] for e in list(FSM['OUTSIDE'].keys())])
    FE_INSIDE_EVENTS = set([e[1] for e in list(FSM['FE_INSIDE'].keys())]).union({EVENT_RESET, EVENT_BAN, EVENT_ALTER_INFO})

    @classmethod
    def get_next_state(cls, operator_type, current_status, event):
        """
        获取下一状态
        :param operator_type: 'OUTSIDE'/'FE_INSIDE'
        :param current_status: 当前状态
        :param event: 条件
        :return: 如果返回None表示错误状态或条件
        """
        fsm = cls.FSM[operator_type]
        next_state_info = fsm.get((current_status, event), None)
        return next_state_info

    @classmethod
    @db.with_transaction
    def update_status(cls, operator_type, shop, event, current_status=None, **kwargs):
        """
        更新对象的状态
        :param operator_type: 'OUTSIDE'/'FE_INSIDE'
        :param shop: Shop 对象
        :param current_status: 当前状态, 如果为None就拿obj的status字段
        :param event: 派件员事件类型
        :param kwargs: 目前支持:
            operator_id: 操作人id
            remark: 操作备注
        :return: obj 或 None, None表示出错
        """
        if current_status is None:
            current_status = shop.status if shop.status else cls.STATUS_INIT
        next_state = cls.get_next_state(operator_type, current_status, event)
        next_status = next_state['next'] if next_state else None

        if operator_type == 'FE_INSIDE':
            # ===> 上帝操作!!! <===
            if event == cls.EVENT_RESET:
                next_status = cls.STATUS_INIT
            # ===> 拉黑操作!!! <===
            elif event == cls.EVENT_BAN:
                next_status = cls.STATUS_BANNED
            # ===> 修改资料!!! <===
            elif event == cls.EVENT_ALTER_INFO:
                next_status = current_status

        # 日志
        debug_str = 'shop_id[%s][%s]: from [%s] to [%s], event[%s].' % (
            shop.id, shop.name, current_status, next_status, event)
        logging.info(debug_str) if next_status else logging.warning(debug_str)

        if next_status:
            # 更新状态
            from_status = current_status
            kwargs['status'] = next_status

            # 过滤掉不需要的字段
            kw = ShopLogic.filter_shop(kwargs,
                                       excludes=('shop_id', 'password'),
                                       includes=('fee__fh', 'fee__ps', 'fee__fh_base'))
            shop.modify(**kw)
            shop.reload()

            # 事件记录
            fsm_log = dict(shop_id=str(shop.pk),
                           shop_name=shop.name,
                           from_status=from_status,
                           to_status=next_status,
                           event=event,
                           operator_type=operator_type,
                           operator_id=kwargs.get('operator_id', ''),
                           remark=kwargs.get('remark', None),
                           create_time=utc_8_now(ret='datetime'))
            ShopFSMLogLogic.create(**fsm_log)

            # 判断是否要发送短信提醒: 有remark的话,添加到文案中.
            if next_state and 'send_sms' in next_state:
                if kwargs.get('remark'):
                    msg = next_state['send_sms'].format(remark=', 理由: %s。' % kwargs['remark'])
                else:
                    msg = next_state['send_sms']
                async_send_sms(shop.tel, msg=msg, sms_type=SMS_TYPE_NORMAL)
            return shop
        else:
            return None

if __name__ == "__main__":
    print((ShopFSM.OUTSIDE_EVENTS))
    print((ShopFSM.FE_INSIDE_EVENTS))
    print((ShopFSM.FE_INSIDE_EVENTS.union(ShopFSM.OUTSIDE_EVENTS)))
