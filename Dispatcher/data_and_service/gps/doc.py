#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-08-26 17:28:27
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo


def unauthorized_error():
    """
        @apiDefine UnauthorizedError
        @apiError (Error 4xx) {401} UnauthorizedError 授权信息出错
        @apiErrorExample 401-UnauthorizedError
            HTTP/1.1 401 UNAUTHORIZED
            {
                "message": "授权信息出错",
                "error_code": 0,
                "content": null
            }
    """


def search_error():
    """
        @apiDefine NotFoundEntityError
        @apiError (Error 4xx) {400} NotFoundEntityError 找不到需要操作的对象
        @apiErrorExample 400-NotFoundEntityError
            HTTP/1.1 400 BAD REQUEST
            {
                "message": "找不到需要操作的对象, 请检查参数",
                "error_code": 4004,
                "content": null
            }
    """

def create_error():
    """
        @apiDefine DuplicateEntryError
        @apiError (Error 4xx) {400} DuplicateEntryError 找不到需要操作的对象
        @apiErrorExample 400-DuplicateEntryError
            HTTP/1.1 400 BAD REQUEST
            {
                "message": "Duplicate entry",
                "error_code": 4008,
                "content": null
            }
    """

def client_error():
    """
        @apiDefine ClientError

        @apiError (Error 4xx) {400} ParamsError 参数解析错误
        @apiErrorExample 400-ParamsError
            HTTP/1.1 400 BAD REQUEST
            {
                "message": "参数解析错误",
                "error_code": 4002,
                "content": null
            }


        @apiError (Error 4xx) {404} NotFoundError 未找到请求的url
        @apiErrorExample 404-NotFoundError
            HTTP/1.1 404 NOT FOUND
            {
                "message": "404 NOT FOUND",
                "error_code": 0,
                "content": null
            }

        @apiError (Error 4xx) {422} UnprocesableEntityError 当创建一个对象时，发生一个验证错误。
        @apiErrorExample 422-UnprocesableEntityError
            HTTP/1.1 422 UNPROCESABLE ENTITY
            {
                "message": "当创建一个对象时，发生一个验证错误",
                "error_code": 4000,
                "content": null
            }
    """


def server_error():
    """
        @apiDefine ServerError
        @apiError (Error 5xx) {500} InternalServerError 服务器发生错误，用户将无法判断发出的请求是否成功。
        @apiErrorExample 500-InternalServerError
            HTTP/1.1 500 INTERNAL SERVER ERROR
            {
                "message": "系统错误",
                "error_code": 0,
                "content": null
            }
    """


def auth_header_mixin():
    """
        @apiDefine AuthHeader

        @apiHeaderExample Auth-Header-Example
            {
                "Authorization": "token 5b42e18555c11dbf2c31403ea6b706a6"
            }
        @apiHeader {string} Authorization 验证身份，格式为"token {token}"，注意"token"后面需要一个空格
    """
    pass


def delete_success_minx():
    """
        @apiDefine DeleteSuccess

        @apiSuccessExample 204-NO-CONTENT
            HTTP/1.1 204 NO CONTENT

    """
