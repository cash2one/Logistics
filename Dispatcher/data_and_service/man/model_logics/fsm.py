# coding:utf-8


import logging

from .logics import ManFSMLogLogic, ManLogic
from tools_lib.common_util.third_party.sms_api import async_send_sms, SMS_TYPE_NORMAL
from tools_lib.transwarp import db
from tools_lib.transwarp.tz import utc_8_now


class ManFSM(object):
    """
    派件员有限状态机
    """
    # === 派件员状态 ===
    # 黑名单
    STATUS_BANNED = 'STATUS_BANNED'
    # 初始状态
    STATUS_INIT = 'STATUS_INIT'
    # 资料已补全
    STATUS_INFO_COMPLETED = 'STATUS_INFO_COMPLETED'
    # 在岗(可申请提现)
    STATUS_WORKING = 'STATUS_WORKING'

    # === 派件员状态转换事件 ===
    # 后台上帝操作, 重置状态为STATUS_INIT(这样就可以重复注册了).
    EVENT_RESET = 'EVENT_RESET'
    # 后台拉黑
    EVENT_BAN = 'EVENT_BAN'
    # APP资料补全/后台资料修改
    EVENT_COMPLETE_INFO = 'EVENT_COMPLETE_INFO'
    # 后台人力判定资料有误
    EVENT_HR_DECIDE_INFO_MISTAKEN = 'EVENT_HR_DECIDE_INFO_MISTAKEN'
    # 后台人力审核通过
    EVENT_HR_DECIDE_YES = 'EVENT_HR_DECIDE_YES'

    # === 状态转换字典, 元素结构: (初始状态，条件): 下一个状态 ===
    FSM = {
        'APP': {
            # [APP]资料补全 - 没补全过
            (STATUS_INIT, EVENT_COMPLETE_INFO): {'next': STATUS_INFO_COMPLETED},
            # [APP]资料补全 - 补全过,没审核过
            (STATUS_INFO_COMPLETED, EVENT_COMPLETE_INFO): {'next': STATUS_INFO_COMPLETED},
        },
        'FE': {
            # [后台]判定资料有误,返回初始状态
            (STATUS_INFO_COMPLETED, EVENT_HR_DECIDE_INFO_MISTAKEN): {'next': STATUS_INIT, 'send_sms': '很遗憾，您提交的资料未通过认证{remark}您可以修改资料并重新提交，感谢您的配合。'},
            # [后台]资料审核通过,进入在岗
            (STATUS_INFO_COMPLETED, EVENT_HR_DECIDE_YES): {'next': STATUS_WORKING, 'send_sms': '恭喜，您的资料已通过认证，感谢您的配合。'},
            # [后台]修改人员资料,不改状态
            # (*, EVENT_COMPLETE_INFO): *,
        }
    }
    APP_EVENTS = set([e[1] for e in list(FSM['APP'].keys())])
    FE_EVENTS = set([e[1] for e in list(FSM['FE'].keys())]).union({EVENT_RESET, EVENT_BAN})

    @classmethod
    def get_next_state(cls, operator_type, current_status, event, **kwargs):
        """
        获取下一状态
        :param operator_type: 'APP'/'FE'
        :param current_status: 当前状态
        :param event: 条件
        :return: 如果返回None表示错误状态或条件
        """
        fsm = cls.FSM[operator_type]
        next_state_info = fsm.get((current_status, event), None)
        return next_state_info

    @classmethod
    @db.with_transaction
    def update_status(cls, operator_type, man, event, current_status=None, **kwargs):
        """
        更新对象的状态
        :param operator_type: 'APP'/'FE'
        :param man: Man 对象
        :param current_status: 当前状态, 如果为None就拿obj的status字段
        :param event: 派件员事件类型
        :param kwargs: 目前支持:
            operator_id: 操作人id
            remark: 操作备注
        :return: obj 或 None, None表示出错
        """
        if current_status is None:
            current_status = man.status if man.status else cls.STATUS_INIT
        # 构造传入状态机本身的参数
        kw = {
            'man_id': man.id,
        }
        next_state = cls.get_next_state(operator_type, current_status, event, **kw)
        next_status = next_state['next'] if next_state else None

        if operator_type == 'FE':
            # ===> 上帝操作!!! <===
            if event == cls.EVENT_RESET:
                next_status = cls.STATUS_INIT
            # ===> 拉黑操作!!! <===
            elif event == cls.EVENT_BAN:
                next_status = cls.STATUS_BANNED
            # ===> 修改资料!!! <===
            elif event == cls.EVENT_COMPLETE_INFO:
                next_status = current_status

        # 日志
        debug_str = 'man_id[%s][%s]: from [%s] to [%s], event[%s].' % (
            man.id, man.name, current_status, next_status, event)
        logging.info(debug_str) if next_status else logging.warning(debug_str)

        if next_status:
            # 更新状态
            from_status = current_status
            kwargs['status'] = next_status
            kw = ManLogic.filter_man(kwargs)
            man.modify(**kw)

            # 事件记录
            fsm_log = dict(man_id=str(man.pk),
                           man_name=man.name,
                           from_status=from_status,
                           to_status=next_status,
                           event=event,
                           operator_type=operator_type,
                           operator_id=kwargs.get('operator_id', ''),
                           remark=kwargs.get('remark', None),
                           create_time=utc_8_now(ret='datetime'))
            ManFSMLogLogic.create(**fsm_log)

            # 判断是否要发送短信提醒: 有remark的话,添加到文案中.
            if next_state and 'send_sms' in next_state:
                if kwargs.get('remark'):
                    msg = next_state['send_sms'].format(remark=', 理由: %s。' % kwargs['remark'])
                else:
                    msg = next_state['send_sms']
                async_send_sms(man.tel, msg=msg, sms_type=SMS_TYPE_NORMAL)
            return man
        else:
            return None


if __name__ == '__main__':
    print((ManFSM.__dict__))
    print((dir(ManFSM)))
