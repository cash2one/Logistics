# coding:utf-8
# 所有涉及机器号及机器IP的都在这里配置，不要在其他配置文件中硬编码
from __future__ import unicode_literals
import os.path
import platform

###############################################################
# 机器号
# 生产环境
PROD_API_NODE = 'iZ258ktujb7Z'

# 测试(API和DB在一台机器)
DEV_NODE = 'iZ255xsf5qrZ'
###############################################################
# 机器IP
# 生产环境
PROD_API_INNER_IP = '10.171.103.109'
PROD_API_OUTER_IP = '182.92.240.69'

PROD_MONGODB_INNER_IP = '10.170.171.199'
PROD_MONGODB_OUTER_IP = '123.56.117.75'

PROD_MYSQL_REDIS_INNER_IP = '10.173.14.210'
PROD_MYSQL_REDIS_OUTER_IP = '123.57.40.134'

PROD_POSTGRESQL_INNER_IP = '10.171.125.72'
PROD_POSTGRESQL_OUTER_IP = '182.92.115.196'

DEV_POSTGRESQL_CONFIG = {
    "host": "101.200.81.41",
    "user": "postgres",
    "password": "gomrwind"
}

PROD_POSTGRESQL_CONFIG = {
    "host": "182.92.115.196",
    "user": "postgres",
    "password": "feng123"
}

# 测试(API和DB在一台机器)
DEV_OUTER_IP = '123.57.45.209'
LOCALHOST_IP = '127.0.0.1'
LOCALHOST_NODE = 'localhost'
###############################################################
# 请求服务端口 (用于线上部署模块知道自己该访问的端口:9099/9199)
PROD_BL_DAS_PORT = '9099'
if os.path.abspath(__file__).startswith('/xvdb'):
    PROD_BL_DAS_PORT = '9199'
else:
    PROD_BL_DAS_PORT = '9099'

# 判断是否是DEBUG环境
CURRENT_NODE = platform.node()
if CURRENT_NODE == PROD_API_NODE:
    # 线上环境, 使用线上生产环境内网IP
    DEBUG = False
    IP_API = PROD_API_INNER_IP
    IP_MONGODB = PROD_MONGODB_INNER_IP
    IP_MYSQL = PROD_MYSQL_REDIS_INNER_IP
    IP_REDIS = PROD_MYSQL_REDIS_INNER_IP
    BL_DAS_PORT = PROD_BL_DAS_PORT
    IP_PORT_API = "http://{ip}:{port}".format(ip=IP_API, port=BL_DAS_PORT)
    CONFIG_POSTGRESQL = PROD_POSTGRESQL_CONFIG
else:
    # 测试环境, 使用线上测试环境测试IP
    DEBUG = True
    IP_API = DEV_OUTER_IP
    IP_MONGODB = DEV_OUTER_IP
    IP_MYSQL = DEV_OUTER_IP
    IP_REDIS = DEV_OUTER_IP
    BL_DAS_PORT = PROD_BL_DAS_PORT
    IP_PORT_API = "http://{ip}:{port}".format(ip=IP_API, port=BL_DAS_PORT)
    CONFIG_POSTGRESQL = DEV_POSTGRESQL_CONFIG


def local_to_online_patch():
    global DEBUG, IP_API, IP_MONGODB, IP_MYSQL, IP_REDIS, IP_PORT_API, CONFIG_POSTGRESQL
    DEBUG = False
    IP_API = PROD_API_OUTER_IP
    IP_MONGODB = PROD_MONGODB_OUTER_IP
    IP_MYSQL = PROD_MYSQL_REDIS_OUTER_IP
    IP_REDIS = PROD_MYSQL_REDIS_OUTER_IP
    BL_DAS_PORT = PROD_BL_DAS_PORT
    IP_PORT_API = "http://{ip}:{port}".format(ip=IP_API, port=BL_DAS_PORT)
    CONFIG_POSTGRESQL = PROD_POSTGRESQL_CONFIG


print("IP_PORT_API=[%s]" % IP_PORT_API)

if __name__ == "__main__":
    print IP_API
    print IP_MONGODB
    print IP_MYSQL
    print IP_REDIS
    print BL_DAS_PORT
    print IP_PORT_API
    print CONFIG_POSTGRESQL

    local_to_online_patch()
    print IP_API
    print IP_MONGODB
    print IP_MYSQL
    print IP_REDIS
    print BL_DAS_PORT
    print IP_PORT_API
    print CONFIG_POSTGRESQL
