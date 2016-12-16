# __author__ = 'mio'

import platform
import logging
from tools_lib.host_info import (LOCALHOST_NODE, LOCALHOST_IP,
    DEV_OUTER_IP, DEV_NODE,
    PROD_BL_DAS_PORT, PROD_API_NODE)


node = platform.node()

DEBUG = TEMPLATE_DEBUG = True
if node == PROD_API_NODE:
    DEBUG = TEMPLATE_DEBUG = False

# ==================
if DEBUG:
    settings = {
        "debug": True,
        "autoreload": True
    }
else:
    settings = {
        "autoreload": False
    }

logging.info("LOGIC_API_HOST %s", PROD_API_NODE)
