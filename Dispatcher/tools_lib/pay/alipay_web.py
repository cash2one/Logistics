# coding:utf-8
import alipay_config as ac
from alipay_web_util import create_direct_pay_by_user, notify_verity


def create_web_trade(order_num, money):
    """
    创建请求支付宝的URL
    :param order_num: 充值订单订单号
    :param money: 充值金额
    :return: 请求支付宝的URL
    """

    # TODO
    # 创建充值订单
    # new_charge_order = create_charge_order_quickly(app_id, user_id, amount, CHARGE_ORDER_TYPE)
    # if not new_charge_order:
    #     return ErrorResponse("can not create charge order")

    # 根据支付宝即时到账接口文档组装符合要求的url
    alipay_url = create_direct_pay_by_user(order_num, 'charge', money)
    if not alipay_url:
        # 组装URL出错，关闭充值订单
        # close_charge_order(new_charge_order.num)
        # return ErrorResponse("can not generate url")
        pass

    # TODO
    # 创建交易流水
    # AlipayDeal.add_or_update(
    #     order_num=new_charge_order.num,
    #     subject=u'充值 %.2f' % amount,
    #     amount=amount,
    #     create_time=TimeZone.utc_now(),
    #     type=ac.DEAL_TYPE['web'],
    #     status=ac.DEAL_STATUS['WAIT_BUYER_PAY'])

    return alipay_url
    # result = {
    #     "url": alipay_url,
    #     "order_num": new_charge_order.num
    # }
    # return JsonResponse(result, status=HTTP_201_CREATED)


def web_trade_notice_handler(post_args):
    """
    支付宝服务器异步通知, 如果没有收到该页面返回的 "success" 字符串，支付宝会在24小时内按一定的时间策略重发通知
    :param post_args: 支付宝POST请求的参数
    :return:
    """
    success, failure = 'success', 'failure'

    ret = {
        'result': success,
        'transact_num': post_args.get('out_trade_no'),
        'trade_no': post_args.get('trade_no')
    }
    try:
        trade_status = post_args['trade_status']

        # 验证签名
        if not notify_verity(post_args):
            ret['result'] = failure
            return ret

        status = ac.DEAL_STATUS.get(trade_status, 0)

        # 支付宝返回支付失败
        if status not in (ac.DEAL_STATUS['TRADE_FINISHED'], ac.DEAL_STATUS['TRADE_SUCCESS']):
            ret['result'] = failure
            return ret

        # 避免重复处理
        # if user_has_paid(order_num):
        #     return HttpResponse(SUCCESS)

        # TODO
        # 更新账户余额

    except Exception:
        pass
    finally:
        ret['result'] = success
        return ret
