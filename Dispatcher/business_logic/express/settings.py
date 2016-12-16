# coding: utf-8
from tools_lib.host_info import DEBUG, IP_API, BL_DAS_PORT, PROD_POSTGRESQL_INNER_IP, PROD_POSTGRESQL_OUTER_IP

if DEBUG is True:
    settings = {
        "debug": True,
        "autoreload": True,
    }
    IP_POSTGRE = PROD_POSTGRESQL_OUTER_IP
else:
    settings = {
        "autoreload": False,
    }
    IP_POSTGRE = PROD_POSTGRESQL_INNER_IP

DAS_API_HOST = "http://%s:%s" % (IP_API, BL_DAS_PORT)

MONGODB_NAME = 'aeolus'
