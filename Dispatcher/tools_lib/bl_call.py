# coding:utf-8



class CallState(object):
    """
    呼叫状态机相关变量.
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

    # 状态("STATUS")->中文名
    STATUS_NAME_MAPPING = {
        STATUS_ALL: "商户已呼叫",
        STATUS_ASSIGNED: "收派员已应答",
        STATUS_BE_IN_PROCESS: "收派员收件中",
        STATUS_CLOSABLE: "该次呼叫可关闭",
        STATUS_CLOSED: "呼叫入口已关闭",
        # STATUS_FORWARDING: "转交呼叫中",
        # STATUS_FORWARD_OK: "已转交",
        # STATUS_FORWARD_FAIL: "转交被拒绝",
    }

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
    EVENT_ZJ = 'EVENT_ZJ'
    EVENT_ACCEPT = 'EVENT_ACCEPT'
    EVENT_REJECT = 'EVENT_REJECT'

    # ==> 一些便利的集合
    OUTSIDE_EVENTS = {EVENT_ASSIGN_TO_ME, EVENT_ADD, EVENT_CANCEL, EVENT_PAY_US, EVENT_SJ, EVENT_CLOSE,
                      EVENT_ZJ, EVENT_ACCEPT, EVENT_REJECT}
    INSIDE_EVENTS = {EVENT_RESET}

    PUBLIC = {STATUS_ALL}
    MINE = {STATUS_ASSIGNED, STATUS_BE_IN_PROCESS, STATUS_CLOSABLE, STATUS_CLOSED}


if __name__ == '__main__':
    pass
