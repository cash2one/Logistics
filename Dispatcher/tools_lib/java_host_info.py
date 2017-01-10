# coding:utf-8

"""
JAVA服务端的测试、线上环境。
"""

from .host_info import DEBUG


# >>>>>>>>>>>>>>>>>>> 基础组 JAVA <<<<<<<<<<<<<<<<<<<<<<

# java develop
DEV_JAVA_SERVER_DOMAIN = "dev.japi.gomrwind.com"

# java production
# PROD_JAVA_SERVER_OUTER_IP = "182.92.115.196"
# PROD_JAVA_SERVER_INNER_IP = "10.171.125.72"
PROD_JAVA_SERVER_INNER_DOMAIN = "japi.gomrwind.com"

SERVER_PORT = "5000"

if DEBUG:
    # 测试环境
    JAVA_PREFIX = "http://{ip}:{port}".format(ip=DEV_JAVA_SERVER_DOMAIN, port=SERVER_PORT)
    print(("You're now in Java-DEV: %s" % JAVA_PREFIX))
else:
    # 线上环境
    JAVA_PREFIX = "http://{ip}:{port}".format(ip=PROD_JAVA_SERVER_INNER_DOMAIN, port=SERVER_PORT)
    print(("You're now in Java-PROD: %s" % JAVA_PREFIX))


# >>>>>>>>>>>>>>>>>>> 数据组 JAVA <<<<<<<<<<<<<<<<<<<<<<

# data java develop
DEV_JAVA_DATA_SERVER_DOMAIN = "dev.japi-data.gomrwind.com"
PROD_JAVA_DATA_SERVER_DOMAIN = "japi-data.gomrwind.com"

JAVA_DATA_SERVER_PORT = "5000"

if DEBUG:
    # 测试环境
    JAVA_DATA_PREFIX = "http://{ip}:{port}".format(ip=DEV_JAVA_DATA_SERVER_DOMAIN, port=JAVA_DATA_SERVER_PORT)
    print(("You're now in Java-Data-DEV: %s" % JAVA_DATA_PREFIX))
else:
    # 线上环境
    JAVA_DATA_PREFIX = "http://{ip}:{port}".format(ip=PROD_JAVA_DATA_SERVER_DOMAIN, port=JAVA_DATA_SERVER_PORT)
    print(("You're now in Java-Data-PROD: %s" % JAVA_DATA_PREFIX))
