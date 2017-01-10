# coding:utf-8



class ExprState(object):
    """
    运单状态机相关变量.
    """
    # === 运单状态 ===
    # 主状态
    STATUS_PRE_CREATED = 'PRE_CREATED'
    STATUS_CREATED = 'CREATED'
    STATUS_SENDING = 'SENDING'
    STATUS_FINISHED = 'FINISHED'
    # 从状态: 请注意从状态值一定不要重复!!!
    SUB_STATUS_PRE_CREATED = 'PRE_CREATED'
    SUB_STATUS_PRE_PRICED = 'PRE_PRICED'
    SUB_STATUS_CREATED = 'CREATED'
    SUB_STATUS_SENDING = 'SENDING'
    SUB_STATUS_DELAY = 'DELAY'
    SUB_STATUS_WAREHOUSE = 'WAREHOUSE'
    SUB_STATUS_FINISHED = 'FINISHED'
    SUB_STATUS_NO_CASH = 'NO_CASH'
    SUB_STATUS_CANCEL = 'CANCEL'
    SUB_STATUS_REFUSE = 'REFUSE'
    SUB_STATUS_TRASH = 'TRASH'
    # 主从关联
    STATUS_PRE_CREATED_PRICED = 'PRE_CREATED.PRICED'
    STATUS_CREATED_CREATED = 'CREATED.CREATED'
    STATUS_SENDING_SENDING = 'SENDING.SENDING'
    STATUS_SENDING_DELAY = 'SENDING.DELAY'
    STATUS_SENDING_WAREHOUSE = 'SENDING.WAREHOUSE'
    STATUS_FINISHED_FINISHED = 'FINISHED.FINISHED'
    STATUS_FINISHED_NO_CASH = 'FINISHED.NO_CASH'
    STATUS_FINISHED_CANCEL = 'FINISHED.CANCEL'
    STATUS_FINISHED_REFUSE = 'FINISHED.REFUSE'
    STATUS_FINISHED_TRASH = 'FINISHED.TRASH'
    # 子状态("SUB_STATUS")->中文名
    STATUS_NAME_MAPPING = {
        SUB_STATUS_PRE_CREATED: "已加单",
        SUB_STATUS_PRE_PRICED: "已定价",
        SUB_STATUS_CREATED: "已支付",
        SUB_STATUS_SENDING: "运输中",
        SUB_STATUS_DELAY: "延迟派件",
        # SUB_STATUS_WAREHOUSE: "入仓",
        SUB_STATUS_FINISHED: "已送达",
        SUB_STATUS_NO_CASH: "不给钱",
        SUB_STATUS_CANCEL: "运单取消",
        SUB_STATUS_REFUSE: "拒收",
        SUB_STATUS_TRASH: "无法送达"
    }

    # === 运单状态转换事件 ===
    # 后台上帝操作: 将单变成初始状态
    EVENT_RESET = 'EVENT_RESET'
    # 后台拒绝给钱操作: 运单审核不通过/客户投诉
    EVENT_NO_CASH = 'EVENT_NO_CASH'
    # 后台指派
    EVENT_ZP = 'EVENT_ZP'
    # 派件员定价
    EVENT_PRICING = 'EVENT_PRICING'
    # 发货人取消运单
    EVENT_CANCEL = 'EVENT_CANCEL'
    # 发货人支付
    EVENT_PAY = 'EVENT_PAY'
    # 收件/抢单/取件/入仓操作
    EVENT_SJ = 'EVENT_SJ'
    EVENT_QD = 'EVENT_QD'
    EVENT_QJ = 'EVENT_QJ'
    EVENT_RC = 'EVENT_RC'
    # 确认妥投操作
    EVENT_TT = 'EVENT_TT'
    # 延迟派件: 客户要求延迟派件/改地址/要求工作日派件
    EVENT_DELAY = 'EVENT_DELAY'
    # 客户拒收: 商品质量问题/收件人取消/货品有误
    EVENT_REFUSE = 'EVENT_REFUSE'
    # 无法妥投: 地址错误/电话错误/无人接听
    EVENT_TRASH = 'EVENT_TRASH'

    # ==> 一些便利的集合
    OUTSIDE_EVENTS = {EVENT_PRICING, EVENT_PAY, EVENT_SJ, EVENT_QD, EVENT_QJ, EVENT_RC, EVENT_CANCEL, EVENT_TT,
                      EVENT_DELAY,
                      EVENT_REFUSE, EVENT_TRASH}
    INSIDE_EVENTS = {EVENT_RESET, EVENT_NO_CASH, EVENT_ZP}

    CREATED = {SUB_STATUS_PRE_CREATED, SUB_STATUS_PRE_PRICED, SUB_STATUS_CREATED}
    SENDING = {SUB_STATUS_SENDING, SUB_STATUS_DELAY, SUB_STATUS_WAREHOUSE}
    FINISHED = {SUB_STATUS_FINISHED, SUB_STATUS_NO_CASH, SUB_STATUS_CANCEL, SUB_STATUS_REFUSE, SUB_STATUS_TRASH}

    @classmethod
    def build_time_name(cls, m_type, event):
        """
        生成要额外记录的时间: 目前只记录EVENT_SJ, EVENT_QJ, EVENT_TT相关
        :param m_type:
        :param event:
        :return:
        """
        if not m_type:
            return None
        # 目前只记录EVENT_SJ, EVENT_QJ, EVENT_TT相关
        elif event not in (cls.EVENT_SJ, cls.EVENT_QJ, cls.EVENT_TT):
            return None
        e = event[6:]
        ret = "_".join([m_type, e, "time"])
        return ret.lower()


if __name__ == '__main__':
    # area_manager_no_cash_time
    print((ExprState.build_time_name('area_manager', ExprState.EVENT_NO_CASH)))
    # parttime_sj_time
    print((ExprState.build_time_name('parttime', ExprState.EVENT_SJ)))
    # parttime_qj_time
    print((ExprState.build_time_name('parttime', ExprState.EVENT_QJ)))
