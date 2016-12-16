#coding=utf-8
__author__ = 'kk'
'''

Periodic tasks scheduled here.

'''

from celery.schedules import crontab
from datetime import timedelta
from tools_lib.host_info import IP_API, PROD_BL_DAS_PORT

# 仓库内部代码的切换: DAS+BL(仅PROD)
DISPATCHER_DAS_BL_PREFIX = "http://{hostip}:{port}".format(hostip=IP_API, port=PROD_BL_DAS_PORT)
# 仓库内部代码的切换: AG(仅5000)
DISPATCHER_AG_PREFIX = "http://{hostip}:{port}".format(hostip=IP_API, port=5000)

# celery时区
CELERY_TIMEZONE = "Asia/Shanghai"

# 定时任务配置
CELERYBEAT_SCHEDULE = {
    # usage sample:
    #
    # "任务描述": {
    #    "task": 一个func(best practice: 通过requests请求你自己的任务接口,而不是直接把代码写在这里)
    #    "schedule": 定时,可以是从运行开始计算周期(timedelta),也可以是按照日期计算周期(crontab)
    #    "args": 参数(list or tuple)
    #    "kwargs": 键值对参数(dict)
    # }
    #
    # crontab usage please refer to:
    #       http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#crontab-schedules

    # '未确认送达订单短信提醒': {
    #     'task': "async_http_request",
    #     'schedule': crontab(hour=19),
    #     "kwargs": {
    #         "method": "post",
    #         "url": DISPATCHER_DAS_BL_PREFIX + "/schedule/logic/wholesale_ec/check_unfinished_expr"
    #     }
    # },

}