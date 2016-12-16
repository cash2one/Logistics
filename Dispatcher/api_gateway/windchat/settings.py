#coding=utf-8
__author__ = 'kk'

import platform
from tools_lib.host_info import (
    LOCALHOST_IP, LOCALHOST_NODE,
    DEV_OUTER_IP, DEV_NODE,
    PROD_API_NODE, PROD_API_INNER_IP, PROD_MONGODB_INNER_IP, PROD_BL_DAS_PORT)

node = platform.node()

if node in (LOCALHOST_NODE, DEV_NODE):
    DEBUG = True
else:
    DEBUG = False

if DEBUG:
    settings = {
        "debug": True,
        "autoreload": True
    }
else:
    settings = {
        "autoreload": False
    }
