#coding=utf-8
__author__ = 'kk'

import logging
import platform
from tools_lib.host_info import LOCALHOST_NODE, DEV_NODE, PROD_API_NODE

__all__ = ["credentials", "dev_credentials", "prod_credentials"]


# 123feng-dev
dev_credentials = {
    "app_id": "q9AGLFWWHa9vYUFbY5i0QsWP-gzGzoHsz",
    "app_key": "JfzkwAsq5nsdVCFTJpNQPbiG",
    "master_key": "5jDxneFQEzdvgjdDyUQs84nd"
}

# 123feng-prod
prod_credentials = {
    "app_id": "VOXtfClUs1dj9N15pI5u6tbg-gzGzoHsz",
    "app_key": "ffpy9fPPKeHszF9qbpPsRUp6",
    "master_key": "oSBV7oPkpy5Lc9v9xGuL67WJ"
}


current_node = platform.node()
if current_node in (LOCALHOST_NODE, DEV_NODE):
    # for debugging/development
    credentials = dev_credentials
    logging.info("leancloud credential for DEV: " + repr(credentials))

elif current_node in (PROD_API_NODE,):
    # for production
    credentials = prod_credentials
    logging.info("leancloud credential for PROD: " + repr(credentials))

else:
    logging.warn("LeanCloud sdk not configured for this host: %s" % current_node)

