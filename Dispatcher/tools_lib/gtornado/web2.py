# coding: utf-8


import json
import logging
import traceback

from concurrent.futures import ThreadPoolExecutor
from schema import Schema, Or, SchemaError, Optional
from tornado.web import RequestHandler
from tornado.web import gen
from tornado.websocket import WebSocketHandler

from tools_lib.gtornado.escape import schema_utf8, schema_utf8_empty
from tools_lib.gtornado.http_code import (is_success,
                                          HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_201_CREATED,
                                          HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN,
                                          HTTP_404_NOT_FOUND
                                          )
from . import async_requests
from ..java_account import AsyncAccount

executor = ThreadPoolExecutor(8)


class RedirectedHTTPResponse(object):
    def __init__(self, response):
        self.request = response.request
        self.code = response.code
        self.reason = response.reason
        self.headers = response.headers
        self.effective_url = response.effective_url
        self.buffer = response.buffer
        self.body = response.body
        self.error = response.error
        self.request_time = response.request_time
        self.time_info = response.time_info
        self.content = response.body  # content默认为未loads的响应body

        if self.body:
            try:
                self.content = json.loads(self.body)
            except Exception as e:
                pass

    def parse_response(self, redirect_header=True):
        # copy headers
        headers = {}
        if redirect_header:
            for key in self.headers:
                if key in ('Date', 'Content-Length', 'Server'):
                    continue
                headers[key] = self.headers[key]
        return self.content, self.code, self.reason, headers


class CommandWSHandler(WebSocketHandler):
    """
    命令-值驱动的WebSocket
    """

    def __init__(self, *args, **kwargs):
        super(CommandWSHandler, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger("answerer_ws_logger")
        self.logger.setLevel(logging.INFO)
        self.logger_handler = logging.StreamHandler()
        self.logger_handler.setFormatter(logging.Formatter(
            '%(levelname)s  %(asctime)s  %(funcName)s:%(lineno)d  WebSocket-ID:' + str(id(self)) + ' %(message)s'))
        self.logger.addHandler(self.logger_handler)

        self.info = logging.info
        self.warn = logging.warn
        self.error = logging.error
        self.critical = logging.critical

    def send(self, command, command_id=None, content=None):
        """
        发送命令
        :param command: 命令名
        :param command_id: 此次操作的唯一标识,用于确认返回
        :param content: 内容
        :return:
        """
        data_to_dump = {
            "command": command,
            "command_id": command_id,
            "content": content
        }
        self.info("[%s]Sending: " % id(self) + repr(data_to_dump))
        data = json.dumps(data_to_dump)
        self.write_message(data)

    @gen.coroutine
    def on_message(self, message):
        """
        处理 command 驱动的 web socket 命令
        :param message:
        :return:
        """
        self.info("[%s]Received: " % id(self) + message)
        try:
            data = json.loads(message)
        except:
            self.error(traceback.format_exc())
            self.send(command="bad-json", content=message)
            raise gen.Return()
        if data == {}:
            # 表示是心跳
            raise gen.Return()
        try:
            data = Schema({
                "command": schema_utf8,
                Optional("command_id", default=""): schema_utf8_empty,
                "content": Or(str, str, list, dict),
            }).validate(data)
        except SchemaError:
            self.send(command="bad-json-schema", content=message)
            self.error("bad json: failed when parsing schema.")
            raise gen.Return()

        command_func = "cmd_" + data["command"].replace("-", "_").lower()
        data.pop("command")
        yield getattr(self, command_func)(**data)


class ReqHandler(RequestHandler):
    """
    业务不相关的 handler,不会也不能验证 token
    """

    def options(self):
        # self.set_header("Access-Control-Allow-Origin", "*")
        # self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        # self.set_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        pass

    def resp(self, content=None, status_code=HTTP_200_OK, reason=None, headers=None):
        """
        HTTP返回
        :param body: 当status_code是2xx时, 则json.dumps,
        否则body的输入可以为一段消息文本, 自动包装成:
        {
            "message": body
        }
        :param status_code: HTTP response状态码
        :param reason:
        :param headers:
        """
        self.set_headers(headers)
        self.set_status(status_code, reason=reason)
        if status_code == HTTP_204_NO_CONTENT:
            # 如果是204的返回, http的标准是不能有body, 所以tornado的httpclient接收的时候会
            # 报错变成599错误
            self.finish()
        elif not is_success(status_code) and isinstance(content, str):
            # 当http code是非正常,且content传进来一个文本的时候,包装成一个含有message键的dict
            self.finish({
                "message": content
            })
        elif isinstance(content, list):
            # 当content是列表(以及其子类的示例)时,认为应当转化为json
            json_body = json.dumps(content, ensure_ascii=False)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self.finish(json_body)
        else:
            # 不然则直接返回
            self.finish(content)

    def resp_error(self, content="", status_code=HTTP_400_BAD_REQUEST, **kwargs):
        """
        通用错误
        """
        self.resp(content=content, status_code=status_code, **kwargs)

    def resp_args_error(self, content="参数解析错误", status_code=HTTP_400_BAD_REQUEST, **kwargs):
        """
        通用错误
        """
        self.resp(content=content, status_code=status_code, **kwargs)

    def resp_created(self, content=""):
        self.resp(content=content, status_code=HTTP_201_CREATED)

    def resp_no_content(self):
        self.resp(status_code=HTTP_204_NO_CONTENT)

    def resp_not_found(self, content="找不到对应的运单"):
        """
        查询id没有结果
        """
        self.resp(content=content, status_code=HTTP_404_NOT_FOUND)

    def resp_unauthorized(self, content="未登录"):
        """
        身份验证失败
        """
        self.resp(content=content, status_code=HTTP_401_UNAUTHORIZED)

    def resp_forbidden(self, content="操作拒绝"):
        """
        被禁止
        """
        self.resp(content=content, status_code=HTTP_403_FORBIDDEN)

    def set_headers(self, headers):
        if headers:
            for header in headers:
                self.set_header(header, headers[header])

    def get_query_args(self):
        """
        获取query_arguments，只取值列表最后一个
        :return:
        """
        return {key: value[-1] for key, value in list(self.request.query_arguments.items())}

    def get_body_args(self):
        """
        获取body_arguments, 只取列表最后一个
        """
        if self.request.body_arguments:
            return {key: value[-1] for key, value in list(self.request.body_arguments.items())}
        elif self.request.body:
            try:
                data = json.loads(self.request.body)
                return data
            except Exception as e:
                logging.fatal(self.request.body)
                raise e
        return {}

    @gen.coroutine
    def resp_redirect(self, http_request=None, redirect_header=True):
        """
        将BL\DAS的接口返回值直接作用于当前请求的返回
        """
        response = yield async_requests.fetch(http_request)
        req = RedirectedHTTPResponse(response)
        self.resp(*req.parse_response(redirect_header))

    @gen.coroutine
    def async_fetch(self, http_request=None):
        """
        请求BL\DAS接口,拿到返回信息
        """
        response = yield async_requests.fetch(http_request)
        resp = RedirectedHTTPResponse(response)
        raise gen.Return(resp)

    def set_x_resource_count(self, n):
        """
        设置分页总数
        :param n:
        """
        if n: self.set_header("X-Resource-Count", str(n))

    def get_app_name(self):
        """
        从headers查出请求的来源App名称
        """
        return self.request.headers.get("app-name", "")


class BusinessReqHandler(ReqHandler):
    """
    业务逻辑AG访问接口
    该 handler 会验证 token 的真实性,但不会在意 token 是哪个角色。
    """

    def get_app_name(self):
        """
        从headers查出请求的来源App名称
        """
        return self.request.headers.get("app-name", "")

    def get_token(self):
        """
        获取 token
        :return: 'token <32位长token>'
        """
        return self.request.headers.get("Authorization", "")

    @gen.coroutine
    def get_user_info_from_token(self, simplified=False):
        account_info = yield AsyncAccount.get_user_info_from_token(self.get_token())
        if not account_info:
            raise gen.Return()  # token 错误或者没给 token, 单纯的返回 None, 不报错。
        if simplified:
            account_info_collected = {i: account_info[i] for i in account_info if i in (
                # 精简字段: 选出需要的字段
                "id",
                "name",
                "tel"
            )}
            account_info_collected["m_type"] = self.get_app_name()
            raise gen.Return(account_info_collected)
        else:
            account_info["m_type"] = self.get_app_name()
            raise gen.Return(account_info)

    @gen.coroutine
    def prepare(self):
        # 当前登录的人员信息
        self.user_info = yield self.get_user_info_from_token()
        if not self.user_info:
            self.resp_unauthorized()
            return
        # 当前登陆人员所绑定的角色tag集合
        self.role_tags = set()
        if self.user_info["roleList"]:
            self.role_tags = set([i["roleTag"] for i in self.user_info["roleList"]])


class ManHandler(ReqHandler):
    def __init__(self, application, request, **kwargs):
        super(ManHandler, self).__init__(application, request, **kwargs)
        self.man_info = None

    @gen.coroutine
    def prepare(self):
        # 从token取配送系人员信息,如无,直接返401
        try:
            token = self.request.headers.get('Authorization')
            if token:
                man_info = yield AsyncAccount.get_basic_from_token({'Authorization': token})
            else:
                self.resp_unauthorized()
                return
        except Exception as e:
            logging.error(e.message)
            self.resp_unauthorized()
        else:
            self.man_info = {k: man_info[k] for k in set(man_info.keys()) & {'id', 'name', 'tel', 'm_type'}}
            self.man_info['m_type'] = self.get_app_name()


class ShopHandler(ReqHandler):
    def __init__(self, application, request, **kwargs):
        super(ShopHandler, self).__init__(application, request, **kwargs)
        self.shop_info = None

    @gen.coroutine
    def prepare(self):
        # 从token取商户基本信息,如无,直接返401
        try:
            token = self.request.headers.get('Authorization')
            if token:
                shop_info = yield AsyncAccount.get_basic_from_token({'Authorization': token})
            else:
                self.resp_unauthorized()
                return
        except Exception as e:
            logging.error(e.message)
            self.resp_unauthorized()
            return
        else:
            self.shop_info = shop_info
            self.shop_info['m_type'] = self.get_app_name()
            return


class StaffHandler(ReqHandler):
    def __init__(self, application, request, **kwargs):
        super(StaffHandler, self).__init__(application, request, **kwargs)
        self.staff_info = None

    @gen.coroutine
    def prepare(self):
        # 从token取职能员工基本信息,如无,直接返401
        try:
            token = self.request.headers.get('Authorization')
            if token:
                staff_info = yield AsyncAccount.get_basic_from_token({'Authorization': token})
            else:
                self.resp_unauthorized()
                return
        except Exception as e:
            logging.error(e.message)
            self.resp_unauthorized()
            return
        else:
            self.staff_info = {k: staff_info[k] for k in set(staff_info.keys()) & {'id', 'name', 'tel'}}
            self.staff_info['m_type'] = self.get_app_name()
