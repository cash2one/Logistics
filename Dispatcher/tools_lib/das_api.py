#!/usr/bin/env python
# coding:utf-8
# import platform
# import requests
# from tools_lib.host_info import IP_API, BL_DAS_PORT, PROD_API_NODE
# from tools_lib.transwarp.web import to_dict
#
# NODE = platform.node()
# TIMEOUT = 0.2 if NODE == PROD_API_NODE else 3.0  # 200 milliseconds if in production

# === configurations ===
# man_service = {
#     'default': 'http://%s:%s' % (IP_API, BL_DAS_PORT),
    # 'localhost': 'http://127.0.0.1:6002',
# }
# shop_service = {
#     'default': 'http://%s:%s' % (IP_API, BL_DAS_PORT),
    # 'localhost': 'http://127.0.0.1:6003'
# }
#
# configs = to_dict({
#     'man_host': man_service.get(NODE, man_service['default']),
#     'shop_host': shop_service.get(NODE, shop_service['default']),
# })


# === 派件员相关 ===
# def get_man_info_from_token(token):
    # 127.0.0.1:6002/deliveryman/token?token=token 6d69042e8d0c6f28471afd9b3c1c0a1e
    # if not token:
    #     return {}
    # url = configs.man_host + '/deliveryman/token'
    # resp = requests.get(url, params=dict(token=token), timeout=TIMEOUT)
    # if resp.status_code == 200:
    #     return resp.json()
    # else:
    #     return {}


# def get_man_info_from_id(man_id, what='BASIC'):
    # what支持的值: "BASIC", "STATUS", "ACCOUNT_LIST", "FAMILIAR_LIST"
    # man_id = str(man_id).strip()
    # 127.0.0.1:6002/deliveryman/outsource/get/basic?id=56b07e84421aa93328c5dcd3
    # url = configs.man_host + '/deliveryman/outsource/get/' + what
    # resp = requests.get(url, params=dict(id=man_id), timeout=TIMEOUT)
    # if resp.status_code == 200:
    #     man_info = resp.json()
    #     return man_info
    # else:
    #     return {}


# === 商户相关 ===
# def get_shop_info_from_token(token):
#     127.0.0.1:6003/shop/token?token=token a1bb6d38f9b48229f2d48cfc6fbad9e4
    # if not token:
    #     return {}
    # url = configs.shop_host + '/shop/token'
    # resp = requests.get(url, params=dict(token=token), timeout=TIMEOUT)
    # if resp.status_code == 200:
    #     ret = resp.json()
        # ret.update(dict(avatar="", accounts=[]))
        # return ret
    # else:
    #     return {}


# def get_shop_info_from_kwargs(**kw):
#     url = configs.shop_host + '/shop/complex_query'
#     allowed = ('shop_id', 'tel')
#     k, v = None, None
#     for k in allowed:
#         if k in kw:
#             v = kw[k]
#             break
#     if not v:
#         raise ValueError("Should provide me with at least one of the following keys%s." % str(allowed))
#
#     k = '_id' if k == 'shop_id' else k
#     query = {
#         k: v
#     }
    # print("query=%s" % query)
    # resp = requests.post(url, json=query, timeout=TIMEOUT)
    # if resp.status_code == 200:
    #     ret = resp.json()
        # return ret[0] if len(ret) == 1 else ret if len(ret) > 1 else {}
        # if isinstance(ret, list):
        #     if len(ret) == 1:
                # ret[0].update(dict(avatar="", accounts=[]))
                # return ret[0]
            # elif len(ret) > 1:
            #     return ret
            # else:
            #     return {}
        # elif isinstance(ret, dict):
            # ret.update(dict(avatar="", accounts=[]))
            # return ret
        # else:
        #     return ret
    # else:
    #     return {}


# 打印最终的配置&Unit Test
# if __name__ == "__main__":
#     import json

    # print("platform.node()=[%s]" % platform.node())
    # print("Configure using:\n%s" % configs)

    # print("从token拿基本信息（派件员）:")
    # print(json.dumps(get_man_info_from_token('token bc5efbd72e6ab2426f65bc258309d79a'), ensure_ascii=False, indent=4))

    # print("从id拿基本信息（派件员）:")
    # print(json.dumps(get_man_info_from_id('56c2e7d97f4525452c8fc23c '), ensure_ascii=False, indent=4))

    # print("从token拿基本信息（商户）:")
    # print(json.dumps(get_shop_info_from_token('token 10d93874017b95ab28dc93addd506395'), ensure_ascii=False, indent=4))

    # print("从shop_id拿基本信息（商户）:")
    # print(json.dumps(get_shop_info_from_kwargs(shop_id="56c2d708a785c90ab0014d00"), ensure_ascii=False, indent=4))

    # print("从tel拿基本信息（商户）:")
    # print(json.dumps(get_shop_info_from_kwargs(tel="13245678902"), ensure_ascii=False, indent=4))
