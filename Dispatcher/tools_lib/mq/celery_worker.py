# -*- coding:utf-8 -*-
from celery import Celery
from tools_lib.gedis.gedis import REDIS_SERVERS
from tools_lib.host_info import CURRENT_NODE

redis_config = REDIS_SERVERS[CURRENT_NODE]


class Config:
    # BROKER_URL = 'redis://:@localhost:6379/0'
    BROKER_URL = 'redis://:{password}@{host}:{port}/{db}'.format(
        password=redis_config.get('password', ''),
        host=redis_config.get('host', ''),
        port=redis_config.get('port', ''),
        db=redis_config.get('db', ''),
    )

    # BROKER_URL = 'redis://:hSu7aX5KN6ZCqGseM8iR1A9gt3vO0jVE@10.0.0.216:6379/1'
    # CELERY_RESULT_BACKEND = 'redis://localhost'
    # CELERYD_HIJACK_ROOT_LOGGER = False
    # CELERY_IGNORE_RESULT = True
    # CELERY_DISABLE_RATE_LIMITS = True
    # CELERYD_CONCURRENCY = 4

    # 路由
    CELERY_ROUTES = {
        'async_http_request': {
            'queue': 'async_request'
        },
    }


app = Celery()
app.config_from_object(Config)
