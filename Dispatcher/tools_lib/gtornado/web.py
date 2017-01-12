#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-09-07 15:19:48
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo
import json
import logging

from concurrent.futures import ThreadPoolExecutor
from schema import Or
from tornado import httpclient
from tornado.web import RequestHandler
from tornado.web import gen

from .error_code import ERR_UNKNOWN, ERR_NO_CONTENT, ERR_ARG, ERR_MULTIPLE_OBJ_RETURNED, ERR_DUPLICATE_ENTRY
from tools_lib.gtornado.http_code import (HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_201_CREATED,
                                          HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_403_FORBIDDEN,
                                          HTTP_500_INTERNAL_SERVER_ERROR, HTTP_401_UNAUTHORIZED)
from . import async_requests

STR_OR_UNICODE = Or(str, str)
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
        self.content = None
        self.error_code = 0
        self.message = ""

        if self.body:
            try:
                body = json.loads(response.body)
                self.content = body['content']
                self.error_code = body['error_code']
                self.message = body['message']
            except Exception:
                self.content = response.body
                self.error_code = 500
                self.message = "服务器开了会小差"

    def parse_response(self, redirect_header=True):
        # copy headers
        headers = {}
        if redirect_header:
            for key in self.headers:
                if key in ('Date', 'Content-Length', 'Content-Type', 'Server'):
                    continue
                # self.add_header(key, response.headers[key])
                headers[key] = self.headers[key]

        return self.content, self.error_code, self.message, self.code, self.reason, headers


class BaseRequestHandler(RequestHandler):
    def options(self):
        # self.set_header("Access-Control-Allow-Origin", "*")
        # self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        # self.set_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        pass

    def write_response(self, content=None, error_code=0, message="",
                       status_code=HTTP_200_OK, reason=None, headers=None):
        self.set_headers(headers)
        self.set_status(status_code, reason=reason)
        if status_code != HTTP_204_NO_CONTENT:
            # 如果是204的返回, http的标准是不能有body, 所以tornado的httpclient接收的时候会
            # 报错变成599错误
            # todo: hard-code
            if error_code == -1:
                self.write(content)
            else:
                self.write(dict(error_code=error_code, message=message, content=content))

    def resp(self, body=None, status_code=HTTP_200_OK, reason=None, headers=None):
        """
        HTTP返回
        :param body: 当status_code是200或201时, 则json.dumps,
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
        elif status_code not in (HTTP_200_OK, HTTP_201_CREATED):
            self.finish({
                "message": body
            })
        else:
            json_body = None # 如果body为None,则默认不写http body
            if body:
                json_body = json.dumps(body, ensure_ascii=False)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self.finish(json_body)

    def error_resp(self, body="", status_code=HTTP_400_BAD_REQUEST, **kwargs):
        """
        用于异常返回的shortcut
        """
        return self.resp(body, status_code, **kwargs)

    def write_error_response(self, content=None, error_code=ERR_UNKNOWN, message="UnknownError",
                             status_code=HTTP_400_BAD_REQUEST, reason=None):
        """
        错误响应
        :param error_code:
        :param message:
        :param status_code:
        :param content:
        :param reason:
        :return:
        """
        self.clear()
        if status_code == HTTP_422_UNPROCESSABLE_ENTITY and not reason:
            reason = message
        self.write_response(content=content, error_code=error_code, message=message,
                            status_code=status_code, reason=reason)
        # self.finish()

    def write_no_content_response(self):
        self.set_status(HTTP_204_NO_CONTENT)

    def write_not_found_entity_response(self, content=None, message="没有找到对应实体"):
        """
        查询id没有结果
        :param content:
        :return:
        """
        self.write_error_response(content=content, error_code=ERR_NO_CONTENT, message=message,
                                  status_code=HTTP_400_BAD_REQUEST)

    def write_multiple_results_found_response(self, content=None):
        """
        查询获取单个数据时，找到不止一个
        :param content:
        :return:
        """
        self.write_error_response(content=content, error_code=ERR_MULTIPLE_OBJ_RETURNED,
                                  message="MultipleObjectsReturned",
                                  status_code=HTTP_400_BAD_REQUEST)

    def write_unprocessable_entity_response(self, content=None):
        """
        创建中的错误
        :param content:
        :return:
        """
        self.write_error_response(content=content, error_code=ERR_UNKNOWN, message="UNPROCESSABLE_ENTITY",
                                  status_code=HTTP_422_UNPROCESSABLE_ENTITY, reason="UNPROCESSABLE_ENTITY")

    def write_parse_args_failed_response(self, message="args parse failed", content=None):
        """
        参数解析错误
        :param content:
        :return:
        """
        self.write_error_response(content=content, error_code=ERR_ARG, message=message,
                                  status_code=HTTP_400_BAD_REQUEST)

    def write_duplicate_entry_response(self, content=None):
        """
        插入操作，重复键值
        :param content:
        :return:
        """
        self.write_error_response(content=content, error_code=ERR_DUPLICATE_ENTRY, message="Duplicate entry",
                                  status_code=HTTP_400_BAD_REQUEST, reason="Duplicate entry")

    def write_unauthorized(self, content=None, message="Unauthorized"):
        """
        身份验证失败
        :param content:
        :param message:
        :return:
        """
        self.write_error_response(content=content, error_code=110, message=message, status_code=HTTP_401_UNAUTHORIZED)

    def write_forbidden_response(self, content=None, message="Forbidden"):
        """
        被禁止
        :param content:
        :return:
        """
        self.write_error_response(content=content, error_code=107, message=message,
                                  status_code=HTTP_403_FORBIDDEN)

    def write_internal_server_error(self, content=None, message="服务器开了会小差"):

        self.write_error_response(content=content, error_code=ERR_UNKNOWN, message=message,
                                  status_code=HTTP_500_INTERNAL_SERVER_ERROR)

    def set_headers(self, headers):
        if headers:
            for header in headers:
                self.set_header(header, headers[header])

    def set_X_Resource_Count(self, n):
        """
        设置分页总数
        :param n:
        """
        if n: self.set_header("X-Resource-Count", str(n))

    def get_token(self):
        try:
            token = self.request.headers.get("Authorization").split(' ')[1]
            return token
        except Exception as e:
            logging.error(e)
            self.write_forbidden_response("Can't get token")
            return False

    def get_query_args(self):
        """
        获取query_arguments，只取值列表最后一个
        :return:
        """
        return {key: value[-1] for key, value in list(self.request.query_arguments.items())}

    def get_body_args(self):
        """
        获取body_arguments, 只取列表最后一个
        :return:
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
    def redirect_request(self, http_request=None, redirect_header=True):
        response = yield async_requests.fetch(http_request)
        req = RedirectedHTTPResponse(response)
        self.write_response(*req.parse_response(redirect_header))
        raise gen.Return(req)

    @gen.coroutine
    def redirect_get(self, url, params=None, redirect_header=True, **kwargs):
        response = yield async_requests.get(url, params=params, **kwargs)
        req = RedirectedHTTPResponse(response)
        self.write_response(*req.parse_response(redirect_header))
        raise gen.Return(req)

    @gen.coroutine
    def redirect_post(self, url, json=None, redirect_header=True, **kwargs):
        response = yield async_requests.post(url, json=json, **kwargs)
        req = RedirectedHTTPResponse(response)
        self.write_response(*req.parse_response(redirect_header))
        raise gen.Return(req)

    @gen.coroutine
    def redirect_patch(self, url, json=None, redirect_header=True, **kwargs):
        response = yield async_requests.patch(url, json=json, **kwargs)
        req = RedirectedHTTPResponse(response)
        self.write_response(*req.parse_response(redirect_header))
        raise gen.Return(req)

    @gen.coroutine
    def redirect_put(self, url, json=None, redirect_header=True, **kwargs):
        response = yield async_requests.put(url, json=json, **kwargs)
        req = RedirectedHTTPResponse(response)
        self.write_response(*req.parse_response(redirect_header))
        raise gen.Return(req)

    @gen.coroutine
    def redirect_delete(self, url, params=None, redirect_header=True, **kwargs):
        response = yield async_requests.delete(url, params=params, **kwargs)
        req = RedirectedHTTPResponse(response)
        self.write_response(*req.parse_response(redirect_header))
        raise gen.Return(req)

    @gen.coroutine
    def das_requests(self, http_request=None):
        response = yield async_requests.fetch(http_request)
        req = RedirectedHTTPResponse(response)
        raise gen.Return(req)

    @gen.coroutine
    def das_get(self, url, params=None, **kwargs):
        response = yield async_requests.get(url, params=params, **kwargs)
        req = RedirectedHTTPResponse(response)
        raise gen.Return(req)


class AGRequestHandler(BaseRequestHandler):
    asyncHTTPClient = httpclient.AsyncHTTPClient()

    @gen.coroutine
    def get_response_list(self, request_list):
        """
        异步，获取列表中的request请求
        :param request_list: [tornado.httpclient.HTTPRequest, ...]
        :return:
        """
        # http_client = httpclient.AsyncHTTPClient()
        response_list = yield [self.asyncHTTPClient.fetch(request) for request in request_list]
        raise gen.Return(response_list)

    @gen.coroutine
    def get_response_dict(self, request_dict):
        """
        异步，获取字典中的request请求
        :param request_dict: {"key": tornado.httpclient.HTTPRequest, ...}
        :return:
        """
        # http_client = httpclient.AsyncHTTPClient()
        response_dict = yield {key: self.asyncHTTPClient.fetch(value) for key, value in list(request_dict.items())}
        raise gen.Return(response_dict)

    def get_app_name(self):
        """
        从headers查出请求的来源App
        """
        return self.request.headers.get("app-name")
