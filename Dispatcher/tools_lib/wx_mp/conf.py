# coding: utf-8
from __future__ import unicode_literals

import logging
from .. import host_info
from wechat_sdk import WechatConf


WECHAT_CONF_PROD = WechatConf(
    token="1qaz2wsx3edc",
    appid="wxeda2f6550280ac63",
    appsecret="8eef8247a26a7887a35ee5e887f38c50",
    encrypt_mode="normal",
    encoding_aes_key="Bn1ZJEljEB8VQOqxkaHJr98iZuJTP8blv3moDLEtEFL"
)

WECHAT_CONF = WECHAT_CONF_PROD

logging.info("WeChat SDK conf: appid==[{appid}]".format(appid=WECHAT_CONF.appid))
