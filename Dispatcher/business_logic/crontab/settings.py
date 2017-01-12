# coding: utf-8

from tools_lib.host_info import DEBUG, IP_API, BL_DAS_PORT
from task import expr_tt_summary, active_shops, node_to_schedule
from task import expr_due_to

if DEBUG is True:
    settings = {
        "debug": True,
        "autoreload": True,
    }
    # 每天N时刻运行 #
    run_at_day = []
else:
    settings = {
        "autoreload": False,
    }
    # 每天N时刻运行 #
    run_at_day = [
        # (node_to_schedule.do_daily_routine_am, (8, 50)),
        # (node_to_schedule.do_daily_routine_pm, (21, 35)),
        (node_to_schedule.do_cliche, (8, 50)),
        (node_to_schedule.do_cliche, (9, 20)),
        (node_to_schedule.do_cliche, (18, 10)),
        (node_to_schedule.do_cliche, (20, 50)),
        # 每天晚上5点发活跃客户数
        (active_shops.send_active_shops_summary, (17, 00)),
        # 每天晚上10点发妥投率表
        (expr_tt_summary.send_tt_summary, (22, 00)),
    ]

DAS_API_HOST = "http://%s:%s" % (IP_API, BL_DAS_PORT)


# 每隔x秒跑
config = [
    # 第二个参数是秒, 第三个参数是启动时是否运行
    (expr_due_to.expr_due_to, 10, True)
]


# 每隔N分钟运行 #

