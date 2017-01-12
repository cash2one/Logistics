# -*- coding:utf-8 -*-

from tools_lib.gedis.gedis import REDIS_SERVERS, CURRENT_NODE
redis_config = REDIS_SERVERS[CURRENT_NODE]

# BROKER_URL = 'redis://:@localhost:6379/0'
BROKER_URL = 'redis://:{password}@{host}:{port}/{db}'.format(
    password=redis_config.get('password', ''),
    host=redis_config.get('host', ''),
    port=redis_config.get('port', ''),
    db=redis_config.get('db', ''),
)
# BROKER_URL = 'redis://:hSu7aX5KN6ZCqGseM8iR1A9gt3vO0jVE@10.0.0.216:6379/1'
# CELERY_RESULT_BACKEND = 'redis://localhost'
CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_IGNORE_RESULT = True
CELERY_DISABLE_RATE_LIMITS = True
# 并发进程数，默认等于CPU核数
# CELERYD_CONCURRENCY = 4
CELERY_ACCEPT_CONTENT = ['json', 'pickle']

# 所有的异步任务定义有放在mq目录下，并把文件加到 CELERY_IMPORTS 配置中
CELERY_IMPORTS = (
    'common_task',
)

from .periodic_task import *