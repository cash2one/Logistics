# coding: utf-8
from __future__ import unicode_literals
from tools_lib.host_info import DEBUG, IP_API, BL_DAS_PORT
from task import invitation, data, settlement, sign_in, node_to_schedule

if DEBUG is True:
    settings = {
        "debug": True,
        "autoreload": True,
    }
else:
    settings = {
        "autoreload": False,
    }

DAS_API_HOST = "http://%s:%s" % (IP_API, BL_DAS_PORT)

MONGODB_NAME = 'aeolus'

# 每隔x秒跑
config = [
    # 第二个参数是秒, 第三个参数是启动时是否运行
]


# 每隔N分钟运行 #


# 每天N时刻运行 #
run_at_day = [
    (node_to_schedule.node_to_schedule, (23, 00))
]