# coding:utf-8

import platform
from tools_lib.host_info import LOCALHOST_NODE, LOCALHOST_IP, IP_API, BL_DAS_PORT, DEBUG

if DEBUG is True:
    settings = {
        "debug": True,
        "autoreload": True,
    }
else:
    settings = {
        "autoreload": False,
    }

current_node = platform.node()
if current_node in (LOCALHOST_NODE,):
    BL_DAS_API_HOST = LOCALHOST_IP
else:
    BL_DAS_API_HOST = IP_API

# BL和DAS共用的url前缀
BL_DAS_API_PREFIX = "http://%s:%s" % (BL_DAS_API_HOST, BL_DAS_PORT)
