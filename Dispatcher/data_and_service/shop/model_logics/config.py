#!/usr/bin/env python
# coding:utf-8
import platform
from tools_lib.host_info import PROD_API_NODE, IP_MYSQL, IP_MONGODB
from tools_lib.transwarp.web import to_dict

NODE = platform.node()

"""DB configurations."""
DB = {
    'default': {
        'mysql': {
            'host': IP_MYSQL,
            'port': 3306,
            'user': 'root',
            'password': 'admindev',
            'database': 'f_shop'
        },
        'mongodb': 'mongodb://%s/profile' % IP_MONGODB,  # default on port 27017
    },
    # PROD
    PROD_API_NODE: {
        'mysql': {
            'host': IP_MYSQL,
            'port': 3306,
            'user': 'fengservice',
            'password': 'sk#u6j%n2x&w9ia',
            'database': 'f_shop'
        },
        'mongodb': 'mongodb://%s/profile' % IP_MONGODB,
    }

}

"""Default DB configurations."""
CONFIGS = DB.get(NODE, DB['default'])
CONFIGS = to_dict(CONFIGS)

# 打印最终的配置
if __name__ == "__main__":
    print(("platform.node()=[%s]" % platform.node()))
    print(("Configure using:\n%s" % CONFIGS))
