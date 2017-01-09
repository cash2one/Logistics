#!/usr/bin/env python
# coding: utf-8


import sys
import os
import json
from wechat_sdk import WechatBasic

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from tools_lib.wx_mp.conf import WECHAT_CONF


wb = WechatBasic(conf=WECHAT_CONF)
with open("menus.json", "r") as z:
    # 默认从当前目录的menus.json文件中读取菜单结构 json 信息
    content = z.read()
menus = json.loads(content)
print(menus)
# 删除线上菜单
wb.delete_menu()
# 创建新菜单
wb.create_menu(menus)