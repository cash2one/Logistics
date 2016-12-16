# coding: utf-8
from tools_lib.host_info import DEBUG, IP_API, BL_DAS_PORT

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

MONGODB_NAME = 'coolie'
