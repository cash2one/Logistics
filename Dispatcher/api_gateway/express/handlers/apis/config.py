# coding=utf-8

from tornado.httpclient import AsyncHTTPClient

async_cli = AsyncHTTPClient()

timeouts = {
    "connect_timeout": 0.5,
    "request_timeout": 3
}

xls_create_expr_timeouts = {
    "connect_timeout": 3,
    "request_timeout": 30
}

wxpay_timeouts = {
    'connect_timeout': 5,
    'request_timeout': 10
}
