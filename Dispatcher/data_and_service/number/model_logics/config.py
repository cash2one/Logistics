#!/usr/bin/env python
# coding:utf-8
import platform
from tools_lib.host_info import PROD_API_NODE, IP_MYSQL
from tools_lib.transwarp.web import to_dict

NODE = platform.node()

"""DB configurations."""
DB = {
    'default': {
        'host': IP_MYSQL,
        'port': 3306,
        'user': 'root',
        'password': 'admindev',
        'database': 'f_deliveryman'
    },
    # PROD
    PROD_API_NODE: {
        'host': IP_MYSQL,
        'port': 3306,
        'user': 'fengservice',
        'password': 'sk#u6j%n2x&w9ia',
        'database': 'f_deliveryman'
    }
}


"""Default configurations."""
DB_CONF = DB.get(NODE, DB['default'])
DEFAULT_CONFIGS = {
    'db': {
        'host': DB_CONF['host'],
        'port': 3306,
        'user': DB_CONF['user'],
        'password': DB_CONF['password'],
        'database': DB_CONF['database']
    }
}


CONFIGS = to_dict(DEFAULT_CONFIGS)


# 打印最终的配置
if __name__ == "__main__":
    print(("platform.node()=[%s]" % platform.node()))
    print(("Configure using:\n%s" % CONFIGS))
