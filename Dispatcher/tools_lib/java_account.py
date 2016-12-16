# coding:utf-8
from __future__ import unicode_literals

import json
import logging

import java_host_info
from schema import Schema, Optional
from tools_lib.common_util import sstring
from tools_lib.gtornado import http_code
from tools_lib.gtornado.escape import schema_unicode, schema_float_empty, schema_unicode_empty
from tornado import gen
from tornado.httpclient import HTTPRequest, HTTPClient, AsyncHTTPClient
from tornado.httputil import url_concat

# http clients
async_cli = AsyncHTTPClient()
sync_cli = HTTPClient()

# request append keywords
timeouts = {
    "connect_timeout": 0.5,
    "request_timeout": 3
}

# request append keywords with header(json content-type)
req_kw_json = dict(timeouts.items() + {
    "headers": {
        "Content-Type": "application/json"
    }
}.items())

# 角色标签
ROLE_TAG_MAN = "man"
ROLE_TAG_DRIVER = "driver"
ROLE_TAG_SHOP = "shop"
ROLE_TAG_STAFF = "staff"
# 全部角色标签列表
ROLE_TAGS = (
    ROLE_TAG_MAN,
    ROLE_TAG_DRIVER,
    ROLE_TAG_SHOP,
    ROLE_TAG_STAFF
)


class AccountRequest(object):
    """
    账户相关的请求体
    """

    @classmethod
    def req_get_user_info_from_token(cls, token):
        """
        根据 token 获取账号信息
        :param token: token形如"token azx21qasw211qsw21qasw2" 或者 "qwesadakfnsdlge"
        :return: None or dict()
        None: 表示找不到该 token 对应的账户
        dict: {
            "id": 内部 id
            "staffNum": 工号
            "name": 姓名
            "tel": 电话
            "status": 状态
        }
        """
        url = java_host_info.JAVA_PREFIX + "/WindCloud/account/token/info"
        if token[:6] == "token ":  # token格式容错
            t = token
        else:
            t = "token " + sstring.safe_utf8(token)
        return HTTPRequest(
            url,
            "GET",
            headers={
                "Authorization": t
            },
            **timeouts
        )

    @classmethod
    def req_get_user_info_from_kwargs(cls, **kwargs):
        """
        根据参数查找账号信息
        :param kwargs:
        可选字段:
        id: 账户 id
        tel: 账户手机号
        :return: None or dict()
        dict: {
            "id": 内部 id
            "staffNum": 工号
            "name": 姓名
            "tel": 电话
            "status": 状态
        }
        """
        user_id = kwargs.get("id")
        if user_id:
            url = java_host_info.JAVA_PREFIX + "/WindCloud/account/user/" + sstring.safe_utf8(user_id)
            return HTTPRequest(
                url,
                "GET",
                **timeouts
            )
        else:
            assert 0

    @classmethod
    def req_complex_query(cls, **kwargs):
        """
        复杂查询账户信息
        :return:
        """
        url = java_host_info.JAVA_PREFIX + "/WindCloud/account/complex_query"
        return HTTPRequest(
            url,
            "POST",
            body=json.dumps(kwargs)
                 ** req_kw_json
        )

    @classmethod
    def req_familiar_points(cls, account_id):
        """
        查询期望工作范围(点)
        :return:
        """
        url = java_host_info.JAVA_PREFIX + "/WindCloud/account/familiar/" + sstring.safe_utf8(account_id)
        return HTTPRequest(
            url,
            "GET",
            **timeouts
        )

    @classmethod
    def req_get_shop_address_info(cls, user_id):
        """
        查询一个商户的发货地址信息
        :param user_id:
        :return:
        """
        url = java_host_info.JAVA_PREFIX + "/WindCloud/addrInfo/send/findByUserId"
        url = url_concat(url, {"userId": user_id})
        return HTTPRequest(
            url,
            "GET",
            **timeouts
        )

    @classmethod
    def req_get_account_by_role(cls, role_tag):
        """
        根据角色查询角色下的全部账户信息
        :param role_tag:
        :return:
        """
        url = java_host_info.JAVA_PREFIX + "/WindCloud/account/role/tag/find"
        url = url_concat(url, {"role_tag": role_tag})
        return HTTPRequest(
            url,
            "GET",
            **timeouts
        )

    @classmethod
    def req_get_basic_from_token(cls, header_authorization):
        """
        根据token获取用户信息
        :param header_authorization: 形如{"Authorization":"token d856728b293a57ca26fbd804117dcee9"}
        :return:
        如果是商户, 会有地址相关信息:
        {
            "id": "56cd130e421aa973b8ccb32c",
            "contact_tel": "",
            "status": "STATUS_INIT",
            "address": "杭州市滨江区星耀城",
            "name": "测试一米鲜",
            "tel": "13282838634",
            "lng": "120.220677",
            "lat": "30.219946"
        },
        否则如果是配送系人员:
        {
            "id": "56cc0f9aeed0932e60a16966",
            "status": "STATUS_WORKING",
            "address": "",
            "name": "达达达",
            "tel": "15658871307",
            "lng": "",
            "lat": ""
        }
        注意: java在请求错误的时候, 也会返回200. 所以200也不能直接判定为成功, 要做返回结果校验
        """
        url = java_host_info.JAVA_PREFIX + '/WindCloud/account/baseInfo/token'
        return HTTPRequest(url, 'GET', headers=header_authorization, **timeouts)

    @classmethod
    def req_get_basic_from_id(cls, user_id):
        """
        根据token获取用户信息
        :param user_id: 形如 "56cd130e421aa973b8ccb32c"
        :return:
        如果是商户, 会有地址相关信息:
        {
            "status": "STATUS_INIT",
            "id": "56cd130e421aa973b8ccb32c",
            "name": "测试一米鲜",
            "tel": "13282838634",
            "contact_tel": "",
            "address": "杭州市滨江区星耀城",
            "lng": "120.220677",
            "lat": "30.219946"
        },
        否则如果是配送系人员:
        {
            "status": "STATUS_WORKING",
            "id": "56cc0f9aeed0932e60a16966",
            "name": "达达达",
            "tel": "15658871307",
            "address": "",
            "lng": "",
            "lat": ""
        }
        注意: java在请求错误的时候, 也会返回200. 所以200也不能直接判定为成功, 要做返回结果校验
        注意: 这里对任何异常都没有检查, 抛出到外部调用者, 调用者直接返401.
        """
        url = java_host_info.JAVA_PREFIX + '/WindCloud/account/baseInfo/id'
        url = url_concat(url, dict(id=user_id))
        return HTTPRequest(url, 'GET', **timeouts)


class SyncAccount(AccountRequest):
    """

    账户相关的阻塞请求
    """

    @classmethod
    def sync_request(cls, req_obj, raise_error=True):
        resp = sync_cli.fetch(req_obj, raise_error=raise_error)
        if not http_code.is_success(resp.code):
            logging.error(">>> sync request returned with non-2xx code <<<")
            logging.error("request: ")
            logging.error(repr(req_obj.__dict__))
            logging.error("response: ")
            logging.error(repr(resp.__dict__))
            return  # java接口访问失败
        return resp

    @classmethod
    def get_user_info_from_token(cls, *args, **kwargs):
        req = cls.req_get_user_info_from_token(*args, **kwargs)
        resp = cls.sync_request(req, raise_error=False)
        try:
            ret = json.loads(resp.body)["account"]
        except:
            return
        return ret

    @classmethod
    def get_basic_from_token(cls, header_authorization):
        """
        根据token获取用户信息
        :param
        header_authorization: 形如
        {"Authorization": "token d856728b293a57ca26fbd804117dcee9"}
        :return:
        如果是商户, 会有地址相关信息:
        {
            "status": "STATUS_INIT",
            "id": "56cd130e421aa973b8ccb32c",
            "name": "测试一米鲜",
            "tel": "13282838634",
            "contact_tel": "",
            "address": "杭州市滨江区星耀城",
            "lng": "120.220677",
            "lat": "30.219946"
        },
        否则如果是配送系人员:
        {
            "status": "STATUS_WORKING",
            "id": "56cc0f9aeed0932e60a16966",
            "name": "达达达",
            "tel": "15658871307",
            "address": "",
            "lng": "",
            "lat": ""
        }

        注意: java在请求错误的时候, 也会返回200.所以200也不能直接判定为成功, 要做返回结果校验
        """

        req = cls.req_get_basic_from_token(header_authorization)
        resp = cls.sync_request(req)

        ret = json.loads(resp.body)
        logging.info(ret)
        ret = Schema({
            "status": schema_unicode_empty,
            "id": schema_unicode,
            Optional("name", default=''): schema_unicode_empty,
            "tel": schema_unicode_empty,
            Optional("contact_tel", default=''): schema_unicode_empty,
            "address": schema_unicode_empty,
            "lng": schema_float_empty,
            "lat": schema_float_empty,
            Optional(object): object
        }).validate(ret)

        # 默认联系电话为注册电话
        if ret['contact_tel'] == '':
            ret['contact_tel'] = ret['tel']
        return ret

    @classmethod
    def get_basic_from_id(cls, user_id):
        """
        根据token获取用户信息
        :param
        id: 形如
        "56cd130e421aa973b8ccb32c"
        :return:
        如果是商户, 会有地址相关信息:
        {
            "status": "STATUS_INIT",
            "id": "56cd130e421aa973b8ccb32c",
            "name": "测试一米鲜",
            "tel": "13282838634",
            "contact_tel": "",
            "address": "杭州市滨江区星耀城",
            "lng": "120.220677",
            "lat": "30.219946"
        },
        否则如果是配送系人员:
        {
            "status": "STATUS_WORKING",
            "id": "56cc0f9aeed0932e60a16966",
            "name": "达达达",
            "tel": "15658871307",
            "address": "",
            "lng": "",
            "lat": ""
        }

        注意: java在请求错误的时候, 也会返回200.所以200也不能直接判定为成功, 要做返回结果校验
        注意: 这里对任何异常都没有检查, 抛出到外部调用者, 调用者直接返401.
        """
        req = cls.req_get_basic_from_id(user_id)
        resp = cls.sync_request(req)

        ret = json.loads(resp.body)
        logging.info(ret)
        ret = Schema({
            "status": schema_unicode_empty,
            "id": schema_unicode,
            Optional("name", default=''): schema_unicode_empty,
            "tel": schema_unicode_empty,
            Optional("contact_tel", default=''): schema_unicode_empty,
            "address": schema_unicode_empty,
            "lng": schema_float_empty,
            "lat": schema_float_empty,
            Optional(object): object
        }).validate(ret)

        # 默认联系电话为注册电话
        if ret['contact_tel'] == '':
            ret['contact_tel'] = ret['tel']
        return ret


class AsyncAccount(AccountRequest):
    """
    账户相关的非阻塞请求
    """

    @classmethod
    @gen.coroutine
    def async_request(cls, req_obj, raise_error=True):
        resp = yield async_cli.fetch(req_obj, raise_error=raise_error)
        if not http_code.is_success(resp.code):
            logging.error(">>> async request returned with non-2xx code <<<")
            logging.error("request: ")
            logging.error(repr(req_obj.__dict__))
            logging.error("response: ")
            logging.error(repr(resp.__dict__))
            raise gen.Return()  # java接口访问失败
        raise gen.Return(resp)

    @classmethod
    @gen.coroutine
    def get_user_info_from_token(cls, *args, **kwargs):
        req = cls.req_get_user_info_from_token(*args, **kwargs)
        resp = yield cls.async_request(req, raise_error=False)
        try:
            ret = json.loads(resp.body)["account"]
        except:
            raise gen.Return()
        raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def get_user_info_from_kwargs(cls, **kwargs):
        req = cls.req_get_user_info_from_kwargs(**kwargs)
        resp = yield cls.async_request(req, raise_error=False)
        try:
            ret = json.loads(resp.body)["account"]
        except:
            raise gen.Return()
        raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def deprecated_complex_query(cls, **kwargs):
        req = cls.req_complex_query(**kwargs)
        resp = yield cls.async_request(req)
        try:
            ret = json.loads(resp.body)["accounts"]
        except:
            raise gen.Return()
        raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def familiar_points(cls, *args, **kwargs):
        req = cls.req_familiar_points(*args, **kwargs)
        resp = yield cls.async_request(req)
        try:
            ret = json.loads(resp.body)["familiar"]
        except:
            raise gen.Return([])
        raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def get_shop_address_info(cls, *args, **kwargs):
        req = cls.req_get_shop_address_info(*args, **kwargs)
        resp = yield cls.async_request(req)
        try:
            ret = json.loads(resp.body)["list"]
        except:
            raise gen.Return([])
        raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def get_account_by_role(cls, *args, **kwargs):
        req = cls.req_get_account_by_role(*args, **kwargs)
        resp = yield cls.async_request(req)
        try:
            ret = json.loads(resp.body)["accounts"]
        except:
            raise gen.Return([])
        raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def get_basic_from_token(cls, header_authorization):
        """
        根据token获取用户信息
        :param
        header_authorization: 形如
        {"Authorization": "token d856728b293a57ca26fbd804117dcee9"}
        :return:
        如果是商户, 会有地址相关信息:
        {
            "status": "STATUS_INIT",
            "id": "56cd130e421aa973b8ccb32c",
            "name": "测试一米鲜",
            "tel": "13282838634",
            "contact_tel": "",
            "address": "杭州市滨江区星耀城",
            "lng": "120.220677",
            "lat": "30.219946"
        },
        否则如果是配送系人员:
        {
            "status": "STATUS_WORKING",
            "id": "56cc0f9aeed0932e60a16966",
            "name": "达达达",
            "tel": "15658871307",
            "address": "",
            "lng": "",
            "lat": ""
        }

        注意: java在请求错误的时候, 也会返回200.所以200也不能直接判定为成功, 要做返回结果校验
        """

        req = cls.req_get_basic_from_token(header_authorization)
        resp = yield cls.async_request(req)

        ret = json.loads(resp.body)

        ret = Schema({
            "status": schema_unicode_empty,
            "id": schema_unicode,
            Optional("name", default=''): schema_unicode_empty,
            "tel": schema_unicode_empty,
            Optional("contact_tel", default=''): schema_unicode_empty,
            "address": schema_unicode_empty,
            "lng": schema_float_empty,
            "lat": schema_float_empty,
            Optional('clientId'): schema_unicode,
            Optional(object): object,
        }).validate(ret)
        logging.info('name=%s, tel=%s' % (ret['name'], ret['tel']))
        # 默认联系电话为注册电话
        if ret['contact_tel'] == '':
            ret['contact_tel'] = ret['tel']
        raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def get_basic_from_id(cls, user_id):
        """
        根据token获取用户信息
        :param
        id: 形如
        "56cd130e421aa973b8ccb32c"
        :return:
        如果是商户, 会有地址相关信息:
        {
            "status": "STATUS_INIT",
            "id": "56cd130e421aa973b8ccb32c",
            "name": "测试一米鲜",
            "tel": "13282838634",
            "contact_tel": "",
            "address": "杭州市滨江区星耀城",
            "lng": "120.220677",
            "lat": "30.219946"
        },
        否则如果是配送系人员:
        {
            "status": "STATUS_WORKING",
            "id": "56cc0f9aeed0932e60a16966",
            "name": "达达达",
            "tel": "15658871307",
            "address": "",
            "lng": "",
            "lat": ""
        }

        注意: java在请求错误的时候, 也会返回200.所以200也不能直接判定为成功, 要做返回结果校验
        注意: 这里对任何异常都没有检查, 抛出到外部调用者, 调用者直接返401.
        """
        req = cls.req_get_basic_from_id(user_id)
        resp = yield cls.async_request(req)

        ret = json.loads(resp.body)
        logging.info(ret)
        ret = Schema({
            "status": schema_unicode_empty,
            "id": schema_unicode,
            Optional("name", default=''): schema_unicode_empty,
            "tel": schema_unicode_empty,
            Optional("contact_tel", default=''): schema_unicode_empty,
            "address": schema_unicode_empty,
            "lng": schema_float_empty,
            "lat": schema_float_empty,
            Optional('clientId'): schema_unicode,
            Optional(object): object,
        }).validate(ret)

        # 默认联系电话为注册电话
        if ret['contact_tel'] == '':
            ret['contact_tel'] = ret['tel']
        raise gen.Return(ret)


if __name__ == '__main__':
    import sys
    from tornado.ioloop import IOLoop
    from functools import partial

    LOGGING_MSG_FORMAT = '%(name)-14s > [%(levelname)s] [%(asctime)s] : %(message)s'
    LOGGING_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format=LOGGING_MSG_FORMAT,
                        datefmt=LOGGING_DATE_FORMAT)
    # 从token取
    f = partial(AsyncAccount.get_basic_from_token, dict(Authorization='token ed104fe249e69fe64ee21676f3da9c49'))
    man = IOLoop.current().run_sync(f)
    print("man: %s\n" % json.dumps(man, ensure_ascii=False, indent=2))

    f = partial(AsyncAccount.get_basic_from_token, dict(Authorization='token ed104fe249e69fe64ee21676f3da9c49'))
    shop = IOLoop.current().run_sync(f)
    print("shop: %s\n" % json.dumps(shop, ensure_ascii=False, indent=2))

    # 从id取
    f = partial(AsyncAccount.get_basic_from_id, '56cc0f9aeed0932e60a16966')
    man = IOLoop.current().run_sync(f)
    print("man: %s\n" % json.dumps(man, ensure_ascii=False, indent=2))

    f = partial(AsyncAccount.get_basic_from_id, '56cd130e421aa973b8ccb32c')
    shop = IOLoop.current().run_sync(f)
    print("shop: %s\n" % json.dumps(shop, ensure_ascii=False, indent=2))

    shop = SyncAccount.get_basic_from_token(dict(Authorization='token d856728b293a57ca26fbd804117dcee9'))
    print("shop: %s\n" % json.dumps(shop, ensure_ascii=False, indent=2))
