#!/usr/bin/env python
# coding:utf-8
import platform
from tools_lib.host_info import PROD_API_NODE, IP_API, BL_DAS_PORT, DEBUG
from tools_lib.transwarp.web import to_dict

NODE = platform.node()
TIMEOUT = 0.7 if NODE == PROD_API_NODE else 7.0  # 500 msecs for prod at most

"""configurations."""
man_service = {
    'default': 'http://%s:%s' % (IP_API, BL_DAS_PORT),
    'localhost': 'http://127.0.0.1:6002',
    PROD_API_NODE: 'http://%s:%s' % (IP_API, BL_DAS_PORT)  # PROD 用线上机器的内网ip
}
shop_service = {
    'default': 'http://%s:%s' % (IP_API, BL_DAS_PORT),
    'localhost': 'http://127.0.0.1:6003',
    PROD_API_NODE: 'http://%s:%s' % (IP_API, BL_DAS_PORT)  # PROD 用线上机器的内网ip
}
express_service = {
    'default': 'http://%s:%s' % (IP_API, BL_DAS_PORT),
    'localhost': 'http://127.0.0.1:5002',
    PROD_API_NODE: 'http://%s:%s' % (IP_API, BL_DAS_PORT)  # PROD 用线上机器的内网ip
}

"""Default configurations."""
default_configs = {
    'man_host': man_service.get(NODE, man_service['default']),
    'shop_host': shop_service.get(NODE, shop_service['default']),
    'express_host': express_service.get(NODE, express_service['default']),
}

CONFIGS = to_dict(default_configs)

# 打印最终的配置
if __name__ == "__main__":
    print("platform.node()=[%s]" % platform.node())
    print("Configure using:\n%s" % CONFIGS)
