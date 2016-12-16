#coding=utf-8
__author__ = 'kk'

import logging

import channel_utils
from tools_lib import java_account
from tools_lib.common_util.third_party.image import get_image_url
from tools_lib.windchat import conf
from tornado import gen
from ..apis import profile

try:
    import ujson as json
except:
    import json


@gen.coroutine
def pack_leancloud_chat_history(data, cli):
    """
    包装leancloud聊天历史
    """
    ret = []
    for i in data:
        msg_data = json.loads(i["data"])
        prof = yield profile.get_man_by_account_id(msg_data["talker_id"])
        msg_data.update({
            "tel": prof.get("tel", None)
        })
        ret.append({
            "msg_id": i["msg-id"],
            "cli": cli,
            "timestamp": i["timestamp"],
            "data": msg_data,
        })
    ret.reverse() # 前端需要拿到翻转的消息历史
    raise gen.Return(ret)

def pack_staff_profile(info):
    """
    包装员工信息
    :param info:
    :return:
    """
    return {
        "talker_type": conf.ACCOUNT_TYPE_STAFF,
        "talker_name": info["name"],
        "talker_id": info["staffNum"],
        "talker_avatar": get_image_url(info["avatarQiniuHash"]),
    }

def pack_man_profile(sorted_ids, unread_last_message_tuple_list, profile_dict_with_client_id_as_key):
    """
    包装配送员的信息
    :param sorted_ids: from sorted-set
    :param unread_last_message_tuple_list: [(unread_count, last_message), ...]
    :return:
    """
    ret = []

    unread_last_message_tuple_list.reverse()
    for i in sorted_ids:
        try:
            current_unread_last = unread_last_message_tuple_list.pop()
        except IndexError:
            current_unread_last = [0, ""]
        try:
            i = profile_dict_with_client_id_as_key[i]
        except:
            continue
        profile_role_tags = [j.get("roleTag") for j in i.get("roleList")]
        if java_account.ROLE_TAG_MAN in profile_role_tags:
            account_type = conf.ACCOUNT_TYPE_MAN
            talker_id = i["id"]
        elif java_account.ROLE_TAG_SHOP in profile_role_tags:
            account_type = conf.ACCOUNT_TYPE_SHOP
            talker_id = i["id"]
        else:
            continue
        logging.warn(i)
        ret.append({
            "client_id": i["client_id"],
            "profile": { # 个人信息
                "talker_id": talker_id,
                "talker_type": account_type,
                "talker_name": i.get("name", ""),
                "talker_avatar": i.get("avatar", ""),
                "tel": i.get("tel", "")
            },
            "unread": current_unread_last[0],
            "last_message": current_unread_last[1]
        })
    return ret

@gen.coroutine
def pack_leancloud_callback_to_ws(data):
    """
    包装 leancloud 发来的消息
    :param data:
    :return:
    """
    ret = []
    for i in data:
        m = json.loads(i["data"])
        lm = channel_utils.CP_unread_count(i["conv"]["objectId"], f=i["from"], t=conf.CHANNEL_PRESENCE_ANY_CLIENT_ID)
        prof = yield profile.get_man_by_account_id(m["talker_id"])
        if not prof or "tel" not in prof.keys():
            prof = yield profile.get_shop_by_account_id(m["talker_id"])
        # logging.info(prof)
        m.update({
            # FIXME hard-code 给推送给前端 ws 的数据加上一些附加数据
            # TODO 以后记得新增列表推送,必须!
            "client_id": i["from"],
            "unread": lm[0],
            "last_message": lm[1],
            "tel": prof["tel"]
        })
        i = {
            "cli": i["conv"]["objectId"],
            "message": m,
            "from": i["from"],
            "msg_id":i["msgId"],
        }
        ret.append(i)
    raise gen.Return(ret)