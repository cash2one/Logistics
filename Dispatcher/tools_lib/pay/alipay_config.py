# coding:utf-8

import platform
from tools_lib.host_info import PROD_API_NODE

if platform.node() == PROD_API_NODE:
    # 手机快捷支付服务器异步通知地址
    # SECURITY_NOTIFY_URL = 'http://api.gomrwind.com:5000/pay/alipay/security/notify'
    # 手机网页支付服务器异步通知地址
    WAP_TOP_UP_NOTIFY_URL = 'http://api.gomrwind.com:5000/shop/wap_top_up_callback'
    WAP_TRANS_NOTIFY_URL = 'http://api.gomrwind.com:5000/shop/wap_transfer_callback'
    # 手机网页支付页面同步通知地址
    # WAP_CALL_BACK_URL = 'http://api.gomrwind.com:5000/shop/top_up_callback'
    # web支付服务器异步通知地址POST
    WEB_NOTIFY_URL = 'http://api.gomrwind.com:5000/shop/web_top_up_callback'
else:
    # 手机快捷支付服务器异步通知地址
    # SECURITY_NOTIFY_URL = 'http://dev.api.gomrwind.com:5000/pay/alipay/security/notify'
    # 手机网页支付服务器异步通知地址
    WAP_TOP_UP_NOTIFY_URL = 'http://dev.api.gomrwind.com:5000/shop/wap_top_up_callback'
    WAP_TRANS_NOTIFY_URL = 'http://dev.api.gomrwind.com:5000/shop/wap_transfer_callback'
    # 手机网页支付页面同步通知地址
    # WAP_CALL_BACK_URL = 'http://dev.api.gomrwind.com:5000/shop/top_up_callback'
    # web支付服务器异步通知地址
    WEB_NOTIFY_URL = 'http://dev.api.gomrwind.com:5000/shop/web_top_up_callback'

# 支付宝网关
ALIPAY_GATEWAY = 'http://wappaygw.alipay.com/service/rest.htm?'
# 支付宝提供给商户的服务接入网关URL()
ALIPAY_GATEWAY_NEW = "https://mapi.alipay.com/gateway.do?"

# 支付宝安全验证地址
ALIPAY_VERIFY_URL = 'https://mapi.alipay.com/gateway.do?service=notify_verify&'

# ==> 以下为格子箱的验证信息
# 商户收款的支付宝账号
EMAIL = 'abcx@123feng.com'
# 支付宝合作身份证ID
PARTNER = '2088901729140845'
# 支付宝交易安全检验码
KEY = 'lvmiz8fk49m69d4r8akg4g5xmq18esnx'
# 支付宝商户私钥
PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIICdwIBADANBgkqhkiG9w0BAQEFAASCAmEwggJdAgEAAoGBAOozqlTm4h3YzkIT
BDjn7yCq9dJcfKCXcZtRsT+XZCHGiwhhpgZpiDVYz0jHdE3JuB8ybiz51xWOHB12
HpRrKZySDMijhtY1N2J6Mg9oyG2CrKD8yQXPN5SyAp5PYPr4Vy9VRsNuVuae1sk3
ZxechvX6R4qRQ+WT1wMIFP1RL3W/AgMBAAECgYEAkFDF5QtgyoOOlaiiMW66K6ct
UzMqmMq5drwgPM9NJILzqXaCl/Dvve+7y10cjdJ/YrnwqkZKAz5OlNj0fwCJ4oMs
7rj/2uEvjTaOiL2T8hqPqZ/EcPEoz4WIQQcw0RJt3cCenUaj1ZEm7XPrOHIT2RPe
HAovK1U4yqnj1jrzDAECQQD9LJ5vysYNifcyaATRXOxNTiNdvuPIGTOFMO3buqbI
tcn55Y6UiLuBATl8xeWD0OYEsUgFBpCnMESFZ9N3P5d5AkEA7NDWYugosY0TADWO
xkzGSgyDAB3oE/Af9+08Uni8boWApnVNXNdSIlG3UWVGmg2fu6CBLTvGfnnqG1Uf
61LQ9wJBAKu0tz/aprhH+f+VzK6x9xH3DMVn0dTEQszygl+kF7nIkVOK/Uh/86tq
yTJ2hVMBOv+zvMSrzy+U7OQNpr4ZwwECQHZRwUuZgvty6NNp7vPU2B2XMryUNKgB
iXdt6H2sJTlzKlwAr657RmYvPdBFMYk21WABSYk4HGyErRsK5O/GaPECQAjzwWWD
y04m1Qrmln8wSrXq/fJKPYN8zb/2oIHRtBesTpB5IAnPgGiNeOkds+iKkU7tyefk
3OFYlMVn1PYH9j0=
-----END PRIVATE KEY-----"""
# 支付宝公钥
ALIPAY_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCnxj/9qwVfgoUh/y2W89L6BkRA
FljhNhgPdyPuBV64bfQNN1PjbCzkIM6qRdKBoLPXmKKMiFYnkd6rAoprih3/PrQE
B/VsW8OoM8fxn67UDYuyBTqA23MML9q1+ilIZwBC2AQ2UBVOrFXfFl75p6/B5Ksi
NG9zpgmLCUYuLkxpLQIDAQAB
-----END PUBLIC KEY-----"""

# ==> 以下为abcx@123feng.com的一个 openapi 对接的 App
# 应用id
APP_ID = "2016062801559836"
APP_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgQDAW12pmc1xY9qpa2ZzoG6dj61Jaqk2OVICLFLL7V4Jh1e4tYMh
VbNVRg7mKzksKQ81n1oijjL3qR2UKtv7fZFgQ9tNqMKLJ9ZtPHspi51hADriM91U
nyIhODFx3MIRL55bqcOQ1+GS3WLwgwwIhSyfHrZmL5HL6iaR4aqbxUaoQQIDAQAB
AoGAcUJat83zhVxCF5dBT7ua5fL/GUdQMrk1bEokxiYRRJMIN53IhAwt93u0shmp
JDNY3T3imI4ZvHE7FU7XEBEzUu+//yk5oR+qGH2J6ufLyRC7ymdQAGI1w7AGIT7p
VKb1tzIIPma1d0vmOriPASM+H8FpUuNGCJMh5+TtBB/y+PECQQD7kC0kX+PjZEIX
81FRJ407N+aNWYGxKCJe1FQe6jPgb8c09xHaTXLcfHYFw/VIycz85zk6I/zHk6De
QpN6kVd/AkEAw7/ekLFzsqiDxyHBPHWOX17Hgv4pDZ7h2+z9cH+AARGPmgiZUmrf
pJGfhCSjKAK8599VorUxqIPZN7RKwo3gPwJAIeDm03E+hY8o/4S7PMywznrWx854
Et2u00qREaDE38Lt9woXE2k+wMbaNiiPzf+vZZfWMyhJkK8nCQe6SNVuDQJAHtC8
q9CToyNuI1IIBomHETJtfAygz9kcOy/ysdwQfZqTHa+O22+hp1mZYAcYfDr6HBKH
e6bEm3+uGVvTjQ8ipwJAN/qBR7t3LA5khM3RNm60W0pPtQyXoeGykZ+QfMHAAUJM
Re6a8QiQkDL/WNr71GCPxPooAS0CMKV5qHwmA7JmOw==
-----END RSA PRIVATE KEY-----"""
APP_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDAW12pmc1xY9qpa2ZzoG6dj61J
aqk2OVICLFLL7V4Jh1e4tYMhVbNVRg7mKzksKQ81n1oijjL3qR2UKtv7fZFgQ9tN
qMKLJ9ZtPHspi51hADriM91UnyIhODFx3MIRL55bqcOQ1+GS3WLwgwwIhSyfHrZm
L5HL6iaR4aqbxUaoQQIDAQAB
-----END PUBLIC KEY-----"""



# ==> 以下为风先生的验证信息
# # 商户收款的支付宝账号
# EMAIL = 'abcf@123feng.com'
# # 支付宝合作身份证ID
# PARTNER = '2088811364424201'
# # 支付宝交易安全检验码
# KEY = 'tnht8jvdrw9kv0ubshcexrz3heolksqv'
# # 支付宝商户私钥
# PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
# MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBANZNyllRKMSMEHq
# US7U17xK9ttmkY1VdXCQx938EAdXEoyLuh96rdU9TJFKr73ObETMUjdHCS5R+1N
# rPZptsvBW38tJkQbjDl8mE8ZuDQ/HIDhHg6RvTJwBUgxaBZ0iS4ibOEvjZk3/hP
# 9xAZy3oTWz1P3dST9YvGNypUwacPAgMBAAECgYA1eUmxicfTa2O9QEAsoF2IlWg
# jQVqr9VTFj1ZDcluG3L8cO0rZ7Aykk4lvu4lPXnUnOsy8d2/miNNP4hQIEbFEfU
# m0hDAkGnSlkHkUEE83d8eBMyZ+K2Uaert+MMzhblj1kAvwjlTXYxyvP5RD5/46d
# /B/guWw0RU+ciL8jGQJBAPD64BSx83/+ITEXPsOXdBEKAfsMFjPhCxiNxQEBK1U
# ZLn3y6Sy4YCp85b0R+lphyu2dcapUBLmH/tCPnjmtfsCQQDjqUQGzEoOTwePZKr
# 3u97CgcNxonoBpsWD99+4dvnbuOUJ//UL6uD/UUfTLcfPpU9qZ9T90dySIyw1Lz
# rAr9AkAPVykkqB9kKn1abqxkLyQIYaa2oJJZQx49teiwo65qgaT34bppBaotUqR
# G7noNfuQ4NCmkOi0C0pF6HWppKY5AkAaO+ca4W+nNnQokfEgPRBbnUwyyi4aDqj
# YgPfGye8A4s2B2XzjYq2KvlMIgr4Dr4j3Of/RP92q+WKevlJQwoBAkEAyL985us
# ZYqYsCCSFOLCdA3NLwBX2ikZZ8Kckae1u9M5a/vGchK32EXJoFFBg06Xbh6BMJu
# NlOlDs+8frGdgw==
# -----END PRIVATE KEY-----"""
# # 支付宝公钥
# ALIPAY_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
# MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCnxj/9qwVfgoUh/y2W89L6BkR
# FljhNhgPdyPuBV64bfQNN1PjbCzkIM6qRdKBoLPXmKKMiFYnkd6rAoprih3/PrQ
# B/VsW8OoM8fxn67UDYuyBTqA23MML9q1+ilIZwBC2AQ2UBVOrFXfFl75p6/B5Ks
# NG9zpgmLCUYuLkxpLQIDAQAB
# -----END PUBLIC KEY-----"""

# 字符编码
INPUT_CHARSET = 'utf-8'

# 签名方式，可选0001(RSA), MD5
SIGN_TYPE = 'MD5'

TRADE_FINISHED = 'TRADE_FINISHED'

WAP_GATEWAY = 'http://wappaygw.alipay.com/service/rest.htm'

DEAL_TYPE = {
    'security': 1,
    'wap': 2,
    'web': 3,
}

DEAL_STATUS = {
    'UNKNOWN': 0,  # 防止支付宝新加状态..
    'WAIT_BUYER_PAY': 1,  # 快捷支付创建交易后发
    'TRADE_CLOSED': 2,  # 不会发, 以防万一
    'TRADE_SUCCESS': 3,  # 高级即时到账
    'TRADE_PENDING': 4,  # 不会发, 以防万一
    'TRADE_FINISHED': 5  # 快捷支付和网页支付付款成功后发
}

# 即时到账支付类型
PAYMENT_TYPE = {
    "buy": 1,  # 商品购买
    "donate": 4,  # 捐赠
    "ecard": 47,  # 电子卡券
}
